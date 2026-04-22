/**
 * Mapanare Package Registry — Cloudflare Workers + R2
 *
 * API:
 *   GET  /v1/packages                      — list all packages
 *   GET  /v1/packages/:name                — package metadata + versions
 *   GET  /v1/packages/:name/:version       — single version metadata
 *   GET  /v1/packages/:name/:version/tar   — download tarball from R2
 *   POST /v1/packages                      — publish (auth required)
 *   GET  /v1/search?q=...                  — substring search
 *   GET  /auth/github?session=...          — start GitHub OAuth
 *   GET  /auth/callback                    — GitHub OAuth callback
 *   GET  /auth/poll?session=...            — poll for auth completion
 */

export interface Env {
  PACKAGES: R2Bucket;
  TOKENS: KVNamespace;
  PACKAGE_INDEX: KVNamespace;
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;
  ALLOWED_PUBLISHERS: string;
}

// --- Types ---

interface PackageVersion {
  version: string;
  sha256: string;
  published_at: string;
  dependencies: Record<string, string>;
  yanked?: boolean;
}

interface PackageMeta {
  name: string;
  description: string;
  license: string;
  repository: string;
  entry: string;
  versions: PackageVersion[];
  latest_version: string;
}

// --- Helpers ---

function json(data: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*", ...headers },
  });
}

function err(message: string, status: number): Response {
  return json({ error: message }, status);
}

async function getPackageMeta(env: Env, name: string): Promise<PackageMeta | null> {
  const raw = await env.PACKAGE_INDEX.get(`pkg:${name}`);
  if (!raw) return null;
  return JSON.parse(raw) as PackageMeta;
}

async function putPackageMeta(env: Env, meta: PackageMeta): Promise<void> {
  await env.PACKAGE_INDEX.put(`pkg:${meta.name}`, JSON.stringify(meta));

  // Update the global package list
  const listRaw = await env.PACKAGE_INDEX.get("pkg:__index__");
  const list: string[] = listRaw ? JSON.parse(listRaw) : [];
  if (!list.includes(meta.name)) {
    list.push(meta.name);
    list.sort();
    await env.PACKAGE_INDEX.put("pkg:__index__", JSON.stringify(list));
  }
}

function tarballKey(name: string, version: string): string {
  return `packages/${name}/${version}/${name}-${version}.tar.gz`;
}

// Simple IP-based rate limiting via KV (per-minute window)
async function checkRateLimit(env: Env, ip: string, limit = 60): Promise<boolean> {
  const minute = Math.floor(Date.now() / 60000);
  const key = `rl:${ip}:${minute}`;
  const raw = await env.TOKENS.get(key);
  const count = raw ? parseInt(raw, 10) : 0;
  if (count >= limit) return false;
  await env.TOKENS.put(key, String(count + 1), { expirationTtl: 120 });
  return true;
}

async function verifyToken(env: Env, token: string): Promise<string | null> {
  const username = await env.TOKENS.get(`token:${token}`);
  return username;
}

// --- Route handlers ---

async function handleListPackages(env: Env): Promise<Response> {
  const listRaw = await env.PACKAGE_INDEX.get("pkg:__index__");
  const names: string[] = listRaw ? JSON.parse(listRaw) : [];

  const packages: { name: string; latest_version: string; description: string }[] = [];
  for (const name of names) {
    const meta = await getPackageMeta(env, name);
    if (meta) {
      packages.push({
        name: meta.name,
        latest_version: meta.latest_version,
        description: meta.description,
      });
    }
  }
  return json({ packages, total: packages.length });
}

async function handleGetPackage(env: Env, name: string): Promise<Response> {
  const meta = await getPackageMeta(env, name);
  if (!meta) return err("package not found", 404);
  return json(meta);
}

async function handleGetVersion(env: Env, name: string, version: string): Promise<Response> {
  const meta = await getPackageMeta(env, name);
  if (!meta) return err("package not found", 404);

  const ver = meta.versions.find((v) => v.version === version);
  if (!ver) return err("version not found", 404);

  return json({
    name: meta.name,
    version: ver.version,
    sha256: ver.sha256,
    tarball_url: `/v1/packages/${encodeURIComponent(name)}/${ver.version}/tar`,
    dependencies: ver.dependencies,
    published_at: ver.published_at,
  });
}

async function handleDownloadTarball(env: Env, name: string, version: string): Promise<Response> {
  const meta = await getPackageMeta(env, name);
  if (!meta) return err("package not found", 404);

  const ver = meta.versions.find((v) => v.version === version);
  if (!ver) return err("version not found", 404);

  const obj = await env.PACKAGES.get(tarballKey(name, version));
  if (!obj) return err("tarball not found in storage", 500);

  return new Response(obj.body, {
    headers: {
      "Content-Type": "application/gzip",
      "Content-Disposition": `attachment; filename="${name}-${version}.tar.gz"`,
      "X-Checksum-Sha256": ver.sha256,
    },
  });
}

async function handlePublish(request: Request, env: Env): Promise<Response> {
  // Auth check
  const authHeader = request.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) {
    return err("missing or invalid Authorization header", 401);
  }
  const token = authHeader.slice(7);
  const username = await verifyToken(env, token);
  if (!username) return err("invalid or expired token", 401);

  // Team-only publishing for MVP
  const allowedOrgs = env.ALLOWED_PUBLISHERS.split(",").map((s) => s.trim());
  const isAllowed = await checkPublisherMembership(username, allowedOrgs);
  if (!isAllowed) {
    return err("publishing is restricted to team members for the MVP", 403);
  }

  // Parse multipart body
  const contentType = request.headers.get("Content-Type") || "";
  if (!contentType.includes("multipart/form-data")) {
    return err("expected multipart/form-data", 400);
  }

  const formData = await request.formData();
  const file = formData.get("file");
  if (!(file instanceof File)) {
    return err("missing 'file' field in form data", 400);
  }

  const tarballBytes = new Uint8Array(await file.arrayBuffer());

  // Parse metadata from the form or extract from tarball
  const nameField = formData.get("name");
  const versionField = formData.get("version");
  const descField = formData.get("description") || "";
  const licenseField = formData.get("license") || "";
  const repoField = formData.get("repository") || "";
  const entryField = formData.get("entry") || "src/lib.mn";
  const depsField = formData.get("dependencies") || "{}";

  if (!nameField || !versionField) {
    return err("missing required fields: name, version", 400);
  }

  const pkgName = nameField.toString();
  const pkgVersion = versionField.toString();

  // Validate package name (alphanumeric + hyphens, 1-64 chars)
  if (!/^[a-z][a-z0-9_-]{0,63}$/.test(pkgName)) {
    return err("invalid package name: must be lowercase alphanumeric with hyphens, 1-64 chars", 400);
  }

  // Validate semver-ish version
  if (!/^\d+\.\d+\.\d+/.test(pkgVersion)) {
    return err("invalid version: must be semver (e.g. 1.2.3)", 400);
  }

  // Check for duplicate version
  const existing = await getPackageMeta(env, pkgName);
  if (existing?.versions.some((v) => v.version === pkgVersion)) {
    return err(`version ${pkgVersion} already exists for ${pkgName}`, 409);
  }

  // Compute SHA-256
  const hashBuffer = await crypto.subtle.digest("SHA-256", tarballBytes);
  const sha256 = Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  // Store tarball in R2
  await env.PACKAGES.put(tarballKey(pkgName, pkgVersion), tarballBytes, {
    httpMetadata: { contentType: "application/gzip" },
    customMetadata: { sha256, publisher: username },
  });

  // Update package index
  let dependencies: Record<string, string> = {};
  try {
    dependencies = JSON.parse(depsField.toString());
  } catch {
    // ignore malformed deps
  }

  const newVersion: PackageVersion = {
    version: pkgVersion,
    sha256,
    published_at: new Date().toISOString(),
    dependencies,
  };

  const meta: PackageMeta = existing || {
    name: pkgName,
    description: descField.toString(),
    license: licenseField.toString(),
    repository: repoField.toString(),
    entry: entryField.toString(),
    versions: [],
    latest_version: pkgVersion,
  };

  meta.versions.push(newVersion);
  // Update latest to highest semver
  meta.versions.sort((a, b) => compareSemver(b.version, a.version));
  meta.latest_version = meta.versions.find((v) => !v.yanked)?.version || pkgVersion;

  // Update description/license/repo if provided on re-publish
  if (descField) meta.description = descField.toString();
  if (licenseField) meta.license = licenseField.toString();
  if (repoField) meta.repository = repoField.toString();

  await putPackageMeta(env, meta);

  return json(
    {
      name: pkgName,
      version: pkgVersion,
      sha256,
      published_at: newVersion.published_at,
    },
    201,
  );
}

async function handleSearch(env: Env, url: URL): Promise<Response> {
  const query = (url.searchParams.get("q") || "").toLowerCase();
  if (!query) return json({ packages: [], total: 0 });

  const listRaw = await env.PACKAGE_INDEX.get("pkg:__index__");
  const names: string[] = listRaw ? JSON.parse(listRaw) : [];

  const results: { name: string; latest_version: string; description: string }[] = [];
  for (const name of names) {
    if (name.toLowerCase().includes(query)) {
      const meta = await getPackageMeta(env, name);
      if (meta) {
        results.push({
          name: meta.name,
          latest_version: meta.latest_version,
          description: meta.description,
        });
      }
      continue;
    }
    // Also check description
    const meta = await getPackageMeta(env, name);
    if (meta && meta.description.toLowerCase().includes(query)) {
      results.push({
        name: meta.name,
        latest_version: meta.latest_version,
        description: meta.description,
      });
    }
  }

  return json({ packages: results, total: results.length });
}

// --- GitHub OAuth ---

async function handleGitHubAuth(env: Env, url: URL): Promise<Response> {
  const session = url.searchParams.get("session");
  if (!session) return err("missing session parameter", 400);

  // Store session as pending
  await env.TOKENS.put(`session:${session}`, "pending", { expirationTtl: 300 });

  const githubUrl =
    `https://github.com/login/oauth/authorize?client_id=${env.GITHUB_CLIENT_ID}` +
    `&scope=read:org&state=${session}`;

  return Response.redirect(githubUrl, 302);
}

async function handleGitHubCallback(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");

  if (!code || !state) return err("missing code or state", 400);

  // Verify session exists
  const sessionStatus = await env.TOKENS.get(`session:${state}`);
  if (!sessionStatus) return err("invalid or expired session", 400);

  // Exchange code for GitHub token
  const tokenResp = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });

  const tokenData = (await tokenResp.json()) as { access_token?: string; error?: string };
  if (!tokenData.access_token) {
    return err("GitHub OAuth failed", 400);
  }

  // Get GitHub username
  const userResp = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${tokenData.access_token}`,
      "User-Agent": "mapanare-registry/0.1",
    },
  });
  const userData = (await userResp.json()) as { login?: string };
  const username = userData.login || "unknown";

  // Generate registry token and store mapping
  const registryToken = crypto.randomUUID() + "-" + crypto.randomUUID();
  await env.TOKENS.put(`token:${registryToken}`, username, { expirationTtl: 86400 * 365 });

  // Mark session as ready with token
  await env.TOKENS.put(
    `session:${state}`,
    JSON.stringify({ status: "ready", token: registryToken, username }),
    { expirationTtl: 300 },
  );

  return new Response(
    `<html><body><h2>Authenticated as ${username}</h2>
     <p>You can close this window and return to the terminal.</p></body></html>`,
    { headers: { "Content-Type": "text/html" } },
  );
}

async function handleAuthPoll(env: Env, url: URL): Promise<Response> {
  const session = url.searchParams.get("session");
  if (!session) return err("missing session", 400);

  const raw = await env.TOKENS.get(`session:${session}`);
  if (!raw) return json({ status: "expired" });
  if (raw === "pending") return json({ status: "pending" });

  try {
    return json(JSON.parse(raw));
  } catch {
    return json({ status: "pending" });
  }
}

// --- Publisher membership check ---

async function checkPublisherMembership(username: string, allowedOrgs: string[]): Promise<boolean> {
  // For MVP, check if user is a member of any allowed GitHub org
  for (const org of allowedOrgs) {
    if (org === username) return true; // Direct username match
    try {
      const resp = await fetch(`https://api.github.com/orgs/${org}/members/${username}`, {
        headers: { "User-Agent": "mapanare-registry/0.1" },
      });
      if (resp.status === 204) return true;
    } catch {
      // continue checking other orgs
    }
  }
  return false;
}

// --- Semver comparison ---

function parseSemver(v: string): [number, number, number] {
  const parts = v.split("-")[0].split("+")[0].split(".");
  return [parseInt(parts[0] || "0"), parseInt(parts[1] || "0"), parseInt(parts[2] || "0")];
}

function compareSemver(a: string, b: string): number {
  const [a1, a2, a3] = parseSemver(a);
  const [b1, b2, b3] = parseSemver(b);
  if (a1 !== b1) return a1 - b1;
  if (a2 !== b2) return a2 - b2;
  return a3 - b3;
}

// --- Router ---

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS preflight
    if (method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
      });
    }

    // Rate limiting
    const clientIp = request.headers.get("CF-Connecting-IP") || "unknown";
    if (!(await checkRateLimit(env, clientIp))) {
      return err("rate limit exceeded", 429);
    }

    // --- Auth routes ---
    if (path === "/auth/github" && method === "GET") {
      return handleGitHubAuth(env, url);
    }
    if (path === "/auth/callback" && method === "GET") {
      return handleGitHubCallback(request, env);
    }
    if (path === "/auth/poll" && method === "GET") {
      return handleAuthPoll(env, url);
    }

    // --- API routes ---
    // POST /v1/packages — publish
    if (path === "/v1/packages" && method === "POST") {
      return handlePublish(request, env);
    }

    // GET /v1/packages — list all
    if (path === "/v1/packages" && method === "GET") {
      return handleListPackages(env);
    }

    // GET /v1/search?q=...
    if (path === "/v1/search" && method === "GET") {
      return handleSearch(env, url);
    }

    // GET /v1/packages/:name/:version/tar — download
    const tarMatch = path.match(/^\/v1\/packages\/([^/]+)\/([^/]+)\/tar$/);
    if (tarMatch && method === "GET") {
      return handleDownloadTarball(env, decodeURIComponent(tarMatch[1]), tarMatch[2]);
    }

    // GET /v1/packages/:name/:version — version info
    const verMatch = path.match(/^\/v1\/packages\/([^/]+)\/([^/]+)$/);
    if (verMatch && method === "GET") {
      return handleGetVersion(env, decodeURIComponent(verMatch[1]), verMatch[2]);
    }

    // GET /v1/packages/:name — package info
    const pkgMatch = path.match(/^\/v1\/packages\/([^/]+)$/);
    if (pkgMatch && method === "GET") {
      return handleGetPackage(env, decodeURIComponent(pkgMatch[1]));
    }

    return err("not found", 404);
  },
};
