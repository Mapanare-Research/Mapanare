/**
 * mapanare_platform.h — Mobile platform detection and tunable defaults
 *
 * Mobile targets (iOS, Android) use smaller defaults to reduce memory
 * footprint.  All values can be overridden via environment variables
 * at runtime, or compile-time defines.
 */

#ifndef MAPANARE_PLATFORM_H
#define MAPANARE_PLATFORM_H

/* -----------------------------------------------------------------------
 * Mobile platform detection
 * ----------------------------------------------------------------------- */

#if defined(__ANDROID__)
  #define MAPANARE_PLATFORM_MOBILE  1
  #define MAPANARE_PLATFORM_ANDROID 1
#elif defined(__APPLE__)
  #include <TargetConditionals.h>
  #if TARGET_OS_IOS || TARGET_OS_TV || TARGET_OS_WATCH
    #define MAPANARE_PLATFORM_MOBILE 1
    #define MAPANARE_PLATFORM_IOS    1
  #endif
#endif

#ifndef MAPANARE_PLATFORM_MOBILE
  #define MAPANARE_PLATFORM_MOBILE 0
#endif

/* -----------------------------------------------------------------------
 * Tunable defaults — override with -D at compile time
 * ----------------------------------------------------------------------- */

/* Default arena block size: 4 KB on mobile, 8 KB on desktop */
#ifndef MAPANARE_DEFAULT_ARENA_BLOCK
  #if MAPANARE_PLATFORM_MOBILE
    #define MAPANARE_DEFAULT_ARENA_BLOCK  4096
  #else
    #define MAPANARE_DEFAULT_ARENA_BLOCK  8192
  #endif
#endif

/* Default ring buffer capacity: 256 on mobile, 1024 on desktop */
#ifndef MAPANARE_DEFAULT_RING_CAPACITY
  #if MAPANARE_PLATFORM_MOBILE
    #define MAPANARE_DEFAULT_RING_CAPACITY  256
  #else
    #define MAPANARE_DEFAULT_RING_CAPACITY  1024
  #endif
#endif

/* Default thread pool: 0 = auto-detect core count on all platforms */
#ifndef MAPANARE_DEFAULT_THREADS
  #if MAPANARE_PLATFORM_MOBILE
    #define MAPANARE_DEFAULT_THREADS  0
  #else
    #define MAPANARE_DEFAULT_THREADS  0  /* 0 = auto-detect core count */
  #endif
#endif

/* Default agent inbox/outbox capacity: 64 on mobile, 256 on desktop */
#ifndef MAPANARE_DEFAULT_AGENT_QUEUE
  #if MAPANARE_PLATFORM_MOBILE
    #define MAPANARE_DEFAULT_AGENT_QUEUE  64
  #else
    #define MAPANARE_DEFAULT_AGENT_QUEUE  256
  #endif
#endif

/* Default signal batch window: 1ms on mobile, 16ms on desktop */
#ifndef MAPANARE_DEFAULT_BATCH_MS
  #if MAPANARE_PLATFORM_MOBILE
    #define MAPANARE_DEFAULT_BATCH_MS  1
  #else
    #define MAPANARE_DEFAULT_BATCH_MS  16
  #endif
#endif

#endif /* MAPANARE_PLATFORM_H */
