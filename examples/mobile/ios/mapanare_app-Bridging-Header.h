/* mapanare_app-Bridging-Header.h -- C FFI for Mapanare static library */

#ifndef MAPANARE_APP_BRIDGING_HEADER_H
#define MAPANARE_APP_BRIDGING_HEADER_H

/* Functions exported by the Mapanare-compiled static library.
 * These correspond to `pub fn` declarations in the .mn source. */
const char *greet(const char *name);
long long compute_in_background(long long input);

#endif
