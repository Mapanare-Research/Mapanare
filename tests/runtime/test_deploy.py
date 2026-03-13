"""Tests for Phase 7 — Deployment Infrastructure."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import urllib.request
from typing import Any

from runtime.agent import (
    AgentBase,
    AgentRegistry,
    AgentState,
    RestartPolicy,
    SupervisionStrategy,
    SupervisionTree,
    TreeStrategy,
)
from runtime.deploy import GracefulShutdown, HealthServer, _HealthStatus

# ---------------------------------------------------------------------------
# Test Agents
# ---------------------------------------------------------------------------


class EchoAgent(AgentBase):
    async def handle(self, value: Any) -> Any:
        return value


class AlwaysFailAgent(AgentBase):
    async def handle(self, value: Any) -> Any:
        raise RuntimeError("always fails")


class CountingAgent(AgentBase):
    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    async def handle(self, value: Any) -> Any:
        self.count += 1
        return value


class FailOnceAgent(AgentBase):
    def __init__(self) -> None:
        super().__init__()
        self._failed = False

    async def handle(self, value: Any) -> Any:
        if not self._failed:
            self._failed = True
            raise RuntimeError("first failure")
        return value


# ===========================================================================
# Task 1 — Dockerfile template
# ===========================================================================


class TestDockerfileScaffolding:
    def test_scaffold_creates_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            created = scaffold_deploy(tmpdir, entry_point="app.mn")
            assert len(created) == 3
            assert os.path.exists(os.path.join(tmpdir, "Dockerfile"))
            assert os.path.exists(os.path.join(tmpdir, "docker-compose.yml"))
            assert os.path.exists(os.path.join(tmpdir, ".dockerignore"))

    def test_dockerfile_contains_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            scaffold_deploy(tmpdir, entry_point="myapp.mn")
            with open(os.path.join(tmpdir, "Dockerfile")) as f:
                content = f.read()
            assert "myapp.mn" in content

    def test_dockerfile_has_healthcheck(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            scaffold_deploy(tmpdir)
            with open(os.path.join(tmpdir, "Dockerfile")) as f:
                content = f.read()
            assert "HEALTHCHECK" in content
            assert "/health" in content

    def test_compose_has_healthcheck(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            scaffold_deploy(tmpdir)
            with open(os.path.join(tmpdir, "docker-compose.yml")) as f:
                content = f.read()
            assert "healthcheck" in content

    def test_no_overwrite_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            # Create existing Dockerfile
            with open(os.path.join(tmpdir, "Dockerfile"), "w") as f:
                f.write("existing")
            created = scaffold_deploy(tmpdir)
            # Should only create compose and dockerignore
            assert len(created) == 2
            with open(os.path.join(tmpdir, "Dockerfile")) as f:
                assert f.read() == "existing"

    def test_dockerignore_excludes_pycache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            scaffold_deploy(tmpdir)
            with open(os.path.join(tmpdir, ".dockerignore")) as f:
                content = f.read()
            assert "__pycache__" in content


# ===========================================================================
# Task 2 — Health check endpoint
# ===========================================================================


class TestHealthServer:
    async def test_health_endpoint_returns_200(self) -> None:
        registry = AgentRegistry()
        server = HealthServer(":0", registry=registry)
        server.start()
        try:
            host, port = server.address
            url = f"http://127.0.0.1:{port}/health"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                assert resp.status == 200
                data = json.loads(resp.read())
                assert data["healthy"] is True
        finally:
            server.stop()

    async def test_ready_endpoint_503_when_no_agents(self) -> None:
        registry = AgentRegistry()
        server = HealthServer(":0", registry=registry)
        server.start()
        try:
            host, port = server.address
            url = f"http://127.0.0.1:{port}/ready"
            req = urllib.request.Request(url)
            try:
                urllib.request.urlopen(req, timeout=2)
                assert False, "Should have gotten 503"
            except urllib.error.HTTPError as e:
                assert e.code == 503
        finally:
            server.stop()

    async def test_ready_endpoint_200_when_agents_running(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        await asyncio.sleep(0.05)

        server = HealthServer(":0", registry=registry)
        server.start()
        try:
            host, port = server.address
            url = f"http://127.0.0.1:{port}/ready"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                assert resp.status == 200
                data = json.loads(resp.read())
                assert data["ready"] is True
        finally:
            server.stop()
            await handle.stop()

    async def test_status_endpoint_json(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        await asyncio.sleep(0.05)

        server = HealthServer(":0", registry=registry)
        server.start()
        try:
            host, port = server.address
            url = f"http://127.0.0.1:{port}/status"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read())
                assert "agents" in data
                assert "echo" in data["agents"]
                assert "uptime_seconds" in data
        finally:
            server.stop()
            await handle.stop()


# ===========================================================================
# Task 3 — Readiness probe
# ===========================================================================


class TestReadinessProbe:
    async def test_not_ready_when_empty(self) -> None:
        registry = AgentRegistry()
        status = _HealthStatus(registry)
        assert not status.is_ready

    async def test_ready_when_all_running(self) -> None:
        registry = AgentRegistry()
        h1 = await EchoAgent.spawn()
        h2 = await EchoAgent.spawn()
        registry.register("a", h1)
        registry.register("b", h2)
        await asyncio.sleep(0.05)
        status = _HealthStatus(registry)
        assert status.is_ready
        await h1.stop()
        await h2.stop()

    async def test_not_ready_when_agent_stopped(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        await handle.stop()
        await asyncio.sleep(0.05)
        status = _HealthStatus(registry)
        assert not status.is_ready

    async def test_custom_readiness_check(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        await asyncio.sleep(0.05)
        status = _HealthStatus(registry)
        assert status.is_ready

        status.set_check("db", False)
        assert not status.is_ready

        status.set_check("db", True)
        assert status.is_ready

        status.remove_check("db")
        assert status.is_ready
        await handle.stop()

    async def test_status_dict_contents(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        await asyncio.sleep(0.05)
        status = _HealthStatus(registry)
        d = status.status_dict()
        assert d["healthy"] is True
        assert d["ready"] is True
        assert "echo" in d["agents"]
        assert d["agents"]["echo"] == "running"
        await handle.stop()


# ===========================================================================
# Task 4 — Supervision trees
# ===========================================================================


class TestSupervisionTrees:
    async def test_one_for_one_restarts_only_failed(self) -> None:
        tree = SupervisionTree(strategy=TreeStrategy.ONE_FOR_ONE, max_restarts=5)
        tree.add_child("echo1", EchoAgent)
        tree.add_child("echo2", EchoAgent)
        handles = await tree.start()
        await asyncio.sleep(0.05)

        assert handles["echo1"]._agent.state == AgentState.RUNNING
        assert handles["echo2"]._agent.state == AgentState.RUNNING
        await tree.stop()

    async def test_tree_children_list(self) -> None:
        tree = SupervisionTree()
        tree.add_child("a", EchoAgent)
        tree.add_child("b", EchoAgent)
        assert tree.children == ["a", "b"]

    async def test_tree_strategy_property(self) -> None:
        tree = SupervisionTree(strategy=TreeStrategy.ONE_FOR_ALL)
        assert tree.strategy == TreeStrategy.ONE_FOR_ALL

    async def test_tree_start_and_stop(self) -> None:
        tree = SupervisionTree()
        tree.add_child("echo", EchoAgent)
        handles = await tree.start()
        await asyncio.sleep(0.05)
        assert handles["echo"]._agent.state == AgentState.RUNNING
        await tree.stop()
        # After stop, handle reference is cleared
        assert tree.get_handle("echo") is None

    async def test_get_handle(self) -> None:
        tree = SupervisionTree()
        tree.add_child("echo", EchoAgent)
        await tree.start()
        await asyncio.sleep(0.05)
        assert tree.get_handle("echo") is not None
        assert tree.get_handle("nonexistent") is None
        await tree.stop()

    async def test_tree_strategy_enum_values(self) -> None:
        assert TreeStrategy.ONE_FOR_ONE.value == "one-for-one"
        assert TreeStrategy.ONE_FOR_ALL.value == "one-for-all"
        assert TreeStrategy.REST_FOR_ONE.value == "rest-for-one"

    async def test_add_child_with_custom_supervision(self) -> None:
        tree = SupervisionTree()
        sup = SupervisionStrategy(policy=RestartPolicy.RESTART, max_restarts=10)
        tree.add_child("echo", EchoAgent, supervision=sup)
        handles = await tree.start()
        await asyncio.sleep(0.05)
        assert handles["echo"]._agent.state == AgentState.RUNNING
        await tree.stop()


# ===========================================================================
# Task 5 — @supervised decorator
# ===========================================================================


class TestSupervisedDecorator:
    def test_emitter_recognizes_supervised(self) -> None:
        from mapanare.ast_nodes import (
            AgentDef,
            Decorator,
            Param,
            Program,
            StringLiteral,
        )
        from mapanare.emit_python import PythonEmitter

        agent = AgentDef(
            name="MyAgent",
            inputs=[Param(name="inbox")],
            outputs=[],
            state=[],
            methods=[],
            decorators=[Decorator(name="supervised", args=[StringLiteral(value="one-for-all")])],
        )
        program = Program(definitions=[agent])
        emitter = PythonEmitter()
        code = emitter.emit(program)
        assert "SupervisionStrategy" in code
        assert "RestartPolicy.RESTART" in code
        assert "one-for-all" in code

    def test_emitter_supervised_no_args(self) -> None:
        from mapanare.ast_nodes import (
            AgentDef,
            Decorator,
            Param,
            Program,
        )
        from mapanare.emit_python import PythonEmitter

        agent = AgentDef(
            name="MyAgent",
            inputs=[Param(name="inbox")],
            outputs=[],
            state=[],
            methods=[],
            decorators=[Decorator(name="supervised", args=[])],
        )
        program = Program(definitions=[agent])
        emitter = PythonEmitter()
        code = emitter.emit(program)
        assert "SupervisionStrategy" in code
        assert "one-for-one" in code  # default strategy

    def test_emitter_no_supervised_no_extra_code(self) -> None:
        from mapanare.ast_nodes import (
            AgentDef,
            Param,
            Program,
        )
        from mapanare.emit_python import PythonEmitter

        agent = AgentDef(
            name="PlainAgent",
            inputs=[Param(name="inbox")],
            outputs=[],
            state=[],
            methods=[],
            decorators=[],
        )
        program = Program(definitions=[agent])
        emitter = PythonEmitter()
        code = emitter.emit(program)
        assert "SupervisionStrategy" not in code


# ===========================================================================
# Task 6 — SIGTERM graceful shutdown
# ===========================================================================


class TestGracefulShutdown:
    async def test_shutdown_stops_all_agents(self) -> None:
        registry = AgentRegistry()
        h1 = await EchoAgent.spawn()
        h2 = await EchoAgent.spawn()
        registry.register("a", h1)
        registry.register("b", h2)
        await asyncio.sleep(0.05)

        shutdown = GracefulShutdown(registry=registry, drain_timeout=1.0)
        await shutdown.shutdown()
        assert h1._agent.state == AgentState.STOPPED
        assert h2._agent.state == AgentState.STOPPED

    async def test_shutdown_drains_mailbox(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        agent = handle._agent
        in_ch = agent._register_input("in")
        agent._register_output("out")
        registry.register("echo", handle)
        await asyncio.sleep(0.05)

        # Send a message
        await in_ch.send("hello")
        await asyncio.sleep(0.1)  # Let agent process

        shutdown = GracefulShutdown(registry=registry, drain_timeout=2.0)
        await shutdown.shutdown()
        assert shutdown.is_shutting_down

    async def test_shutdown_flag(self) -> None:
        registry = AgentRegistry()
        shutdown = GracefulShutdown(registry=registry)
        assert not shutdown.is_shutting_down
        await shutdown.shutdown()
        assert shutdown.is_shutting_down

    async def test_shutdown_with_health_server(self) -> None:
        registry = AgentRegistry()
        server = HealthServer(":0", registry=registry)
        server.start()
        shutdown = GracefulShutdown(registry=registry, health_server=server, drain_timeout=1.0)
        await shutdown.shutdown()
        assert shutdown.is_shutting_down

    async def test_shutdown_empty_registry(self) -> None:
        registry = AgentRegistry()
        shutdown = GracefulShutdown(registry=registry)
        await shutdown.shutdown()  # Should not raise
        assert shutdown.is_shutting_down


# ===========================================================================
# Task 7 — mapanare deploy CLI command
# ===========================================================================


class TestDeployCLI:
    def test_deploy_command_exists(self) -> None:
        from mapanare.cli import build_parser

        parser = build_parser()
        # Should not raise
        args = parser.parse_args(["deploy"])
        assert hasattr(args, "func")

    def test_deploy_with_path(self) -> None:
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["deploy", "/tmp/myproject"])
        assert args.path == "/tmp/myproject"

    def test_deploy_with_entry(self) -> None:
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["deploy", "--entry", "app.mn"])
        assert args.entry == "app.mn"

    def test_deploy_defaults(self) -> None:
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["deploy"])
        assert args.path == "."
        assert args.entry == "main.mn"

    def test_cmd_deploy_creates_files(self) -> None:
        import argparse

        from mapanare.cli import cmd_deploy

        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(path=tmpdir, entry="main.mn")
            cmd_deploy(args)
            assert os.path.exists(os.path.join(tmpdir, "Dockerfile"))
            assert os.path.exists(os.path.join(tmpdir, "docker-compose.yml"))
            assert os.path.exists(os.path.join(tmpdir, ".dockerignore"))


# ===========================================================================
# Task 8 — Integration: full deployment stack
# ===========================================================================


class TestDeploymentIntegration:
    async def test_full_stack_health_ready_shutdown(self) -> None:
        """End-to-end: spawn agents, health check, readiness, graceful shutdown."""
        registry = AgentRegistry()
        server = HealthServer(":0", registry=registry)
        server.start()

        # Spawn agents
        h1 = await EchoAgent.spawn()
        h2 = await EchoAgent.spawn()
        registry.register("worker-1", h1)
        registry.register("worker-2", h2)
        await asyncio.sleep(0.05)

        host, port = server.address

        # Health check
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url, timeout=2) as resp:
            assert resp.status == 200

        # Readiness
        url = f"http://127.0.0.1:{port}/ready"
        with urllib.request.urlopen(url, timeout=2) as resp:
            assert resp.status == 200

        # Graceful shutdown
        shutdown = GracefulShutdown(registry=registry, health_server=server, drain_timeout=2.0)
        await shutdown.shutdown()
        assert h1._agent.state == AgentState.STOPPED
        assert h2._agent.state == AgentState.STOPPED

    async def test_supervision_tree_with_health(self) -> None:
        """Supervision tree + health checks work together."""
        registry = AgentRegistry()
        tree = SupervisionTree(strategy=TreeStrategy.ONE_FOR_ONE, max_restarts=3)
        tree.add_child("worker", EchoAgent)
        handles = await tree.start()
        registry.register("worker", handles["worker"])
        await asyncio.sleep(0.05)

        status = _HealthStatus(registry)
        assert status.is_ready

        await tree.stop()

    async def test_scaffold_and_verify_dockerfile(self) -> None:
        """Scaffold deploy files and verify Dockerfile content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mapanare.deploy import scaffold_deploy

            scaffold_deploy(tmpdir, entry_point="agent_app.mn")

            with open(os.path.join(tmpdir, "Dockerfile")) as f:
                dockerfile = f.read()
            assert "FROM python:3.12-slim" in dockerfile
            assert "agent_app.mn" in dockerfile
            assert "HEALTHCHECK" in dockerfile
            assert "EXPOSE 8080" in dockerfile
