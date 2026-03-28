/**
 * mapanare_gpu.h — GPU compute runtime for Mapanare (Phase 5.2)
 *
 * Provides real GPU compute via runtime-loaded CUDA and Vulkan:
 *   - CUDA Driver API: PTX kernel loading and execution
 *   - Vulkan Compute: SPIR-V shader dispatch
 *   - GPU memory management (device alloc/free/copy)
 *   - Tensor operation dispatch to GPU backends
 *
 * All GPU libraries are loaded via dlopen/LoadLibrary at runtime —
 * no compile-time dependency on CUDA SDK or Vulkan SDK.
 * Graceful fallback to CPU when GPU libraries are not available.
 */

#ifndef MAPANARE_GPU_H
#define MAPANARE_GPU_H

#include <stdint.h>
#include <stddef.h>
#include "mapanare_runtime.h"

/* -----------------------------------------------------------------------
 * Export macro
 * ----------------------------------------------------------------------- */

#ifdef _WIN32
  #define MN_GPU_EXPORT __declspec(dllexport)
#else
  #define MN_GPU_EXPORT __attribute__((visibility("default")))
#endif

/* -----------------------------------------------------------------------
 * 1. CUDA Driver API Typedefs
 *
 * These match the CUDA Driver API signatures. We load them at runtime
 * via dlopen("libcuda.so") / LoadLibrary("nvcuda.dll").
 * Using the _v2 variants which are current since CUDA 3.2+.
 * ----------------------------------------------------------------------- */

/** CUDA result code. */
typedef int CUresult;

/** Opaque CUDA types (matching driver API). */
typedef int          CUdevice;
typedef void        *CUcontext;
typedef void        *CUmodule;
typedef void        *CUfunction;
typedef uint64_t     CUdeviceptr;

/** CUDA Driver API function pointer types. */
typedef CUresult (*pfn_cuInit)(unsigned int flags);
typedef CUresult (*pfn_cuDeviceGetCount)(int *count);
typedef CUresult (*pfn_cuDeviceGet)(CUdevice *device, int ordinal);
typedef CUresult (*pfn_cuDeviceGetName)(char *name, int len, CUdevice dev);
typedef CUresult (*pfn_cuDeviceTotalMem_v2)(size_t *bytes, CUdevice dev);
typedef CUresult (*pfn_cuCtxCreate_v2)(CUcontext *pctx, unsigned int flags, CUdevice dev);
typedef CUresult (*pfn_cuCtxDestroy_v2)(CUcontext ctx);
typedef CUresult (*pfn_cuCtxSetCurrent)(CUcontext ctx);
typedef CUresult (*pfn_cuModuleLoadDataEx)(CUmodule *module, const void *image,
                                           unsigned int numOptions,
                                           int *options, void **optionValues);
typedef CUresult (*pfn_cuModuleUnload)(CUmodule hmod);
typedef CUresult (*pfn_cuModuleGetFunction)(CUfunction *hfunc, CUmodule hmod,
                                            const char *name);
typedef CUresult (*pfn_cuMemAlloc_v2)(CUdeviceptr *dptr, size_t bytesize);
typedef CUresult (*pfn_cuMemFree_v2)(CUdeviceptr dptr);
typedef CUresult (*pfn_cuMemcpyHtoD_v2)(CUdeviceptr dstDevice, const void *srcHost,
                                         size_t byteCount);
typedef CUresult (*pfn_cuMemcpyDtoH_v2)(void *dstHost, CUdeviceptr srcDevice,
                                         size_t byteCount);
typedef CUresult (*pfn_cuLaunchKernel)(CUfunction f,
                                       unsigned int gridDimX, unsigned int gridDimY,
                                       unsigned int gridDimZ,
                                       unsigned int blockDimX, unsigned int blockDimY,
                                       unsigned int blockDimZ,
                                       unsigned int sharedMemBytes,
                                       void *hStream,
                                       void **kernelParams, void **extra);
typedef CUresult (*pfn_cuCtxSynchronize)(void);

/* -----------------------------------------------------------------------
 * 2. Vulkan Compute Typedefs
 *
 * Minimal subset of the Vulkan API needed for compute dispatch.
 * Loaded via dlopen("libvulkan.so") / LoadLibrary("vulkan-1.dll").
 * We define only what we need — no full vulkan.h dependency.
 * ----------------------------------------------------------------------- */

/** Vulkan result code. */
typedef int32_t VkResult;

/** Vulkan boolean. */
typedef uint32_t VkBool32;

/** Opaque Vulkan handle types. */
typedef struct VkInstance_T       *VkInstance;
typedef struct VkPhysicalDevice_T *VkPhysicalDevice;
typedef struct VkDevice_T         *VkDevice;
typedef struct VkQueue_T          *VkQueue;
typedef struct VkCommandPool_T    *VkCommandPool;
typedef struct VkCommandBuffer_T  *VkCommandBuffer;
typedef struct VkBuffer_T         *VkBuffer;
typedef struct VkDeviceMemory_T   *VkDeviceMemory;
typedef struct VkShaderModule_T   *VkShaderModule;
typedef struct VkPipelineLayout_T *VkPipelineLayout;
typedef struct VkPipeline_T       *VkPipeline;
typedef struct VkDescriptorSetLayout_T *VkDescriptorSetLayout;
typedef struct VkDescriptorPool_T      *VkDescriptorPool;
typedef struct VkDescriptorSet_T       *VkDescriptorSet;
typedef struct VkFence_T               *VkFence;
typedef uint64_t VkDeviceSize;

/** Vulkan application info (minimal). */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_APPLICATION_INFO = 0 */
    const void *pNext;
    const char *pApplicationName;
    uint32_t    applicationVersion;
    const char *pEngineName;
    uint32_t    engineVersion;
    uint32_t    apiVersion;
} MnVkApplicationInfo;

/** Vulkan instance create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO = 1 */
    const void *pNext;
    uint32_t    flags;
    const MnVkApplicationInfo *pApplicationInfo;
    uint32_t    enabledLayerCount;
    const char * const *ppEnabledLayerNames;
    uint32_t    enabledExtensionCount;
    const char * const *ppEnabledExtensionNames;
} MnVkInstanceCreateInfo;

/** Vulkan physical device properties (minimal). */
typedef struct {
    uint32_t apiVersion;
    uint32_t driverVersion;
    uint32_t vendorID;
    uint32_t deviceID;
    uint32_t deviceType;        /* VkPhysicalDeviceType */
    char     deviceName[256];
    uint8_t  pipelineCacheUUID[16];
    /* ... trimmed — we only read deviceName and deviceType */
    uint8_t  _padding[512];     /* oversize to handle full struct */
} MnVkPhysicalDeviceProperties;

/** Vulkan device queue create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO = 2 */
    const void *pNext;
    uint32_t    flags;
    uint32_t    queueFamilyIndex;
    uint32_t    queueCount;
    const float *pQueuePriorities;
} MnVkDeviceQueueCreateInfo;

/** Vulkan device create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO = 3 */
    const void *pNext;
    uint32_t    flags;
    uint32_t    queueCreateInfoCount;
    const MnVkDeviceQueueCreateInfo *pQueueCreateInfos;
    uint32_t    enabledLayerCount;
    const char * const *ppEnabledLayerNames;
    uint32_t    enabledExtensionCount;
    const char * const *ppEnabledExtensionNames;
    const void *pEnabledFeatures;
} MnVkDeviceCreateInfo;

/** Vulkan shader module create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO = 16 */
    const void *pNext;
    uint32_t    flags;
    size_t      codeSize;       /* in bytes (must be multiple of 4) */
    const uint32_t *pCode;      /* SPIR-V bytecode */
} MnVkShaderModuleCreateInfo;

/** Vulkan buffer create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO = 12 */
    const void *pNext;
    uint32_t    flags;
    VkDeviceSize size;
    uint32_t    usage;
    uint32_t    sharingMode;
    uint32_t    queueFamilyIndexCount;
    const uint32_t *pQueueFamilyIndices;
} MnVkBufferCreateInfo;

/** Vulkan memory allocate info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO = 5 */
    const void *pNext;
    VkDeviceSize allocationSize;
    uint32_t    memoryTypeIndex;
} MnVkMemoryAllocateInfo;

/** Vulkan memory requirements. */
typedef struct {
    VkDeviceSize size;
    VkDeviceSize alignment;
    uint32_t     memoryTypeBits;
} MnVkMemoryRequirements;

/** Vulkan physical device memory properties. */
typedef struct {
    uint32_t memoryTypeCount;
    struct {
        uint32_t propertyFlags;
        uint32_t heapIndex;
    } memoryTypes[32];
    uint32_t memoryHeapCount;
    struct {
        VkDeviceSize size;
        uint32_t     flags;
    } memoryHeaps[16];
} MnVkPhysicalDeviceMemoryProperties;

/** Vulkan submit info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_SUBMIT_INFO = 4 */
    const void *pNext;
    uint32_t    waitSemaphoreCount;
    const void *pWaitSemaphores;
    const uint32_t *pWaitDstStageMask;
    uint32_t    commandBufferCount;
    const VkCommandBuffer *pCommandBuffers;
    uint32_t    signalSemaphoreCount;
    const void *pSignalSemaphores;
} MnVkSubmitInfo;

/** Vulkan command buffer allocate info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO = 40 */
    const void *pNext;
    VkCommandPool commandPool;
    uint32_t      level;        /* VK_COMMAND_BUFFER_LEVEL_PRIMARY = 0 */
    uint32_t      commandBufferCount;
} MnVkCommandBufferAllocateInfo;

/** Vulkan command buffer begin info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO = 42 */
    const void *pNext;
    uint32_t    flags;          /* VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT = 1 */
    const void *pInheritanceInfo;
} MnVkCommandBufferBeginInfo;

/** Vulkan command pool create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO = 39 */
    const void *pNext;
    uint32_t    flags;
    uint32_t    queueFamilyIndex;
} MnVkCommandPoolCreateInfo;

/** Vulkan compute pipeline create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO = 29 */
    const void *pNext;
    uint32_t    flags;
    struct {
        int32_t  sType;         /* VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO = 18 */
        const void *pNext;
        uint32_t    flags;
        uint32_t    stage;      /* VK_SHADER_STAGE_COMPUTE_BIT = 0x20 */
        VkShaderModule module;
        const char  *pName;     /* entry point name, typically "main" */
        const void  *pSpecializationInfo;
    } stage;
    VkPipelineLayout layout;
    VkPipeline basePipelineHandle;
    int32_t    basePipelineIndex;
} MnVkComputePipelineCreateInfo;

/** Vulkan descriptor set layout binding. */
typedef struct {
    uint32_t binding;
    uint32_t descriptorType;    /* VK_DESCRIPTOR_TYPE_STORAGE_BUFFER = 7 */
    uint32_t descriptorCount;
    uint32_t stageFlags;        /* VK_SHADER_STAGE_COMPUTE_BIT = 0x20 */
    const void *pImmutableSamplers;
} MnVkDescriptorSetLayoutBinding;

/** Vulkan descriptor set layout create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO = 32 */
    const void *pNext;
    uint32_t    flags;
    uint32_t    bindingCount;
    const MnVkDescriptorSetLayoutBinding *pBindings;
} MnVkDescriptorSetLayoutCreateInfo;

/** Vulkan pipeline layout create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO = 30 */
    const void *pNext;
    uint32_t    flags;
    uint32_t    setLayoutCount;
    const VkDescriptorSetLayout *pSetLayouts;
    uint32_t    pushConstantRangeCount;
    const void *pPushConstantRanges;
} MnVkPipelineLayoutCreateInfo;

/** Vulkan descriptor pool size. */
typedef struct {
    uint32_t type;              /* VK_DESCRIPTOR_TYPE_STORAGE_BUFFER = 7 */
    uint32_t descriptorCount;
} MnVkDescriptorPoolSize;

/** Vulkan descriptor pool create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO = 33 */
    const void *pNext;
    uint32_t    flags;
    uint32_t    maxSets;
    uint32_t    poolSizeCount;
    const MnVkDescriptorPoolSize *pPoolSizes;
} MnVkDescriptorPoolCreateInfo;

/** Vulkan descriptor set allocate info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO = 34 */
    const void *pNext;
    VkDescriptorPool descriptorPool;
    uint32_t    descriptorSetCount;
    const VkDescriptorSetLayout *pSetLayouts;
} MnVkDescriptorSetAllocateInfo;

/** Vulkan descriptor buffer info. */
typedef struct {
    VkBuffer     buffer;
    VkDeviceSize offset;
    VkDeviceSize range;
} MnVkDescriptorBufferInfo;

/** Vulkan write descriptor set. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET = 35 */
    const void *pNext;
    VkDescriptorSet dstSet;
    uint32_t    dstBinding;
    uint32_t    dstArrayElement;
    uint32_t    descriptorCount;
    uint32_t    descriptorType;
    const void *pImageInfo;
    const MnVkDescriptorBufferInfo *pBufferInfo;
    const void *pTexelBufferView;
} MnVkWriteDescriptorSet;

/** Vulkan fence create info. */
typedef struct {
    int32_t  sType;             /* VK_STRUCTURE_TYPE_FENCE_CREATE_INFO = 8 */
    const void *pNext;
    uint32_t    flags;
} MnVkFenceCreateInfo;

/** Vulkan Driver API function pointer types. */
typedef VkResult (*pfn_vkCreateInstance)(const MnVkInstanceCreateInfo *, const void *,
                                        VkInstance *);
typedef VkResult (*pfn_vkDestroyInstance)(VkInstance, const void *);
typedef VkResult (*pfn_vkEnumeratePhysicalDevices)(VkInstance, uint32_t *, VkPhysicalDevice *);
typedef void     (*pfn_vkGetPhysicalDeviceProperties)(VkPhysicalDevice,
                                                      MnVkPhysicalDeviceProperties *);
typedef void     (*pfn_vkGetPhysicalDeviceMemoryProperties)(VkPhysicalDevice,
                                                            MnVkPhysicalDeviceMemoryProperties *);
typedef VkResult (*pfn_vkCreateDevice)(VkPhysicalDevice, const MnVkDeviceCreateInfo *,
                                       const void *, VkDevice *);
typedef void     (*pfn_vkDestroyDevice)(VkDevice, const void *);
typedef void     (*pfn_vkGetDeviceQueue)(VkDevice, uint32_t, uint32_t, VkQueue *);
typedef VkResult (*pfn_vkCreateShaderModule)(VkDevice, const MnVkShaderModuleCreateInfo *,
                                             const void *, VkShaderModule *);
typedef void     (*pfn_vkDestroyShaderModule)(VkDevice, VkShaderModule, const void *);
typedef VkResult (*pfn_vkCreateComputePipelines)(VkDevice, void *,
                                                  uint32_t,
                                                  const MnVkComputePipelineCreateInfo *,
                                                  const void *, VkPipeline *);
typedef void     (*pfn_vkDestroyPipeline)(VkDevice, VkPipeline, const void *);
typedef VkResult (*pfn_vkCreatePipelineLayout)(VkDevice, const MnVkPipelineLayoutCreateInfo *,
                                               const void *, VkPipelineLayout *);
typedef void     (*pfn_vkDestroyPipelineLayout)(VkDevice, VkPipelineLayout, const void *);
typedef VkResult (*pfn_vkCreateDescriptorSetLayout)(VkDevice,
                                                     const MnVkDescriptorSetLayoutCreateInfo *,
                                                     const void *, VkDescriptorSetLayout *);
typedef void     (*pfn_vkDestroyDescriptorSetLayout)(VkDevice, VkDescriptorSetLayout,
                                                      const void *);
typedef VkResult (*pfn_vkCreateDescriptorPool)(VkDevice, const MnVkDescriptorPoolCreateInfo *,
                                                const void *, VkDescriptorPool *);
typedef void     (*pfn_vkDestroyDescriptorPool)(VkDevice, VkDescriptorPool, const void *);
typedef VkResult (*pfn_vkAllocateDescriptorSets)(VkDevice,
                                                  const MnVkDescriptorSetAllocateInfo *,
                                                  VkDescriptorSet *);
typedef void     (*pfn_vkUpdateDescriptorSets)(VkDevice, uint32_t,
                                                const MnVkWriteDescriptorSet *,
                                                uint32_t, const void *);
typedef VkResult (*pfn_vkCreateCommandPool)(VkDevice, const MnVkCommandPoolCreateInfo *,
                                             const void *, VkCommandPool *);
typedef void     (*pfn_vkDestroyCommandPool)(VkDevice, VkCommandPool, const void *);
typedef VkResult (*pfn_vkAllocateCommandBuffers)(VkDevice,
                                                  const MnVkCommandBufferAllocateInfo *,
                                                  VkCommandBuffer *);
typedef VkResult (*pfn_vkBeginCommandBuffer)(VkCommandBuffer,
                                              const MnVkCommandBufferBeginInfo *);
typedef VkResult (*pfn_vkEndCommandBuffer)(VkCommandBuffer);
typedef void     (*pfn_vkCmdBindPipeline)(VkCommandBuffer, uint32_t, VkPipeline);
typedef void     (*pfn_vkCmdBindDescriptorSets)(VkCommandBuffer, uint32_t, VkPipelineLayout,
                                                 uint32_t, uint32_t, const VkDescriptorSet *,
                                                 uint32_t, const uint32_t *);
typedef void     (*pfn_vkCmdDispatch)(VkCommandBuffer, uint32_t, uint32_t, uint32_t);
typedef VkResult (*pfn_vkQueueSubmit)(VkQueue, uint32_t, const MnVkSubmitInfo *, VkFence);
typedef VkResult (*pfn_vkQueueWaitIdle)(VkQueue);
typedef VkResult (*pfn_vkCreateBuffer)(VkDevice, const MnVkBufferCreateInfo *,
                                        const void *, VkBuffer *);
typedef void     (*pfn_vkDestroyBuffer)(VkDevice, VkBuffer, const void *);
typedef void     (*pfn_vkGetBufferMemoryRequirements)(VkDevice, VkBuffer,
                                                       MnVkMemoryRequirements *);
typedef VkResult (*pfn_vkAllocateMemory)(VkDevice, const MnVkMemoryAllocateInfo *,
                                          const void *, VkDeviceMemory *);
typedef void     (*pfn_vkFreeMemory)(VkDevice, VkDeviceMemory, const void *);
typedef VkResult (*pfn_vkBindBufferMemory)(VkDevice, VkBuffer, VkDeviceMemory, VkDeviceSize);
typedef VkResult (*pfn_vkMapMemory)(VkDevice, VkDeviceMemory, VkDeviceSize, VkDeviceSize,
                                     uint32_t, void **);
typedef void     (*pfn_vkUnmapMemory)(VkDevice, VkDeviceMemory);
typedef VkResult (*pfn_vkCreateFence)(VkDevice, const MnVkFenceCreateInfo *,
                                       const void *, VkFence *);
typedef void     (*pfn_vkDestroyFence)(VkDevice, VkFence, const void *);
typedef VkResult (*pfn_vkWaitForFences)(VkDevice, uint32_t, const VkFence *, VkBool32,
                                         uint64_t);
typedef VkResult (*pfn_vkResetFences)(VkDevice, uint32_t, const VkFence *);
typedef VkResult (*pfn_vkResetCommandBuffer)(VkCommandBuffer, uint32_t);

/* -----------------------------------------------------------------------
 * 3. CUDA Function Table
 * ----------------------------------------------------------------------- */

typedef struct mn_cuda_fns {
    pfn_cuInit                cuInit;
    pfn_cuDeviceGetCount      cuDeviceGetCount;
    pfn_cuDeviceGet           cuDeviceGet;
    pfn_cuDeviceGetName       cuDeviceGetName;
    pfn_cuDeviceTotalMem_v2   cuDeviceTotalMem;
    pfn_cuCtxCreate_v2        cuCtxCreate;
    pfn_cuCtxDestroy_v2       cuCtxDestroy;
    pfn_cuCtxSetCurrent       cuCtxSetCurrent;
    pfn_cuModuleLoadDataEx    cuModuleLoadDataEx;
    pfn_cuModuleUnload        cuModuleUnload;
    pfn_cuModuleGetFunction   cuModuleGetFunction;
    pfn_cuMemAlloc_v2         cuMemAlloc;
    pfn_cuMemFree_v2          cuMemFree;
    pfn_cuMemcpyHtoD_v2      cuMemcpyHtoD;
    pfn_cuMemcpyDtoH_v2      cuMemcpyDtoH;
    pfn_cuLaunchKernel        cuLaunchKernel;
    pfn_cuCtxSynchronize      cuCtxSynchronize;
} mn_cuda_fns_t;

/* -----------------------------------------------------------------------
 * 4. Vulkan Function Table
 * ----------------------------------------------------------------------- */

typedef struct mn_vulkan_fns {
    pfn_vkCreateInstance                 vkCreateInstance;
    pfn_vkDestroyInstance                vkDestroyInstance;
    pfn_vkEnumeratePhysicalDevices       vkEnumeratePhysicalDevices;
    pfn_vkGetPhysicalDeviceProperties    vkGetPhysicalDeviceProperties;
    pfn_vkGetPhysicalDeviceMemoryProperties vkGetPhysicalDeviceMemoryProperties;
    pfn_vkCreateDevice                   vkCreateDevice;
    pfn_vkDestroyDevice                  vkDestroyDevice;
    pfn_vkGetDeviceQueue                 vkGetDeviceQueue;
    pfn_vkCreateShaderModule             vkCreateShaderModule;
    pfn_vkDestroyShaderModule            vkDestroyShaderModule;
    pfn_vkCreateComputePipelines         vkCreateComputePipelines;
    pfn_vkDestroyPipeline                vkDestroyPipeline;
    pfn_vkCreatePipelineLayout           vkCreatePipelineLayout;
    pfn_vkDestroyPipelineLayout          vkDestroyPipelineLayout;
    pfn_vkCreateDescriptorSetLayout      vkCreateDescriptorSetLayout;
    pfn_vkDestroyDescriptorSetLayout     vkDestroyDescriptorSetLayout;
    pfn_vkCreateDescriptorPool           vkCreateDescriptorPool;
    pfn_vkDestroyDescriptorPool          vkDestroyDescriptorPool;
    pfn_vkAllocateDescriptorSets         vkAllocateDescriptorSets;
    pfn_vkUpdateDescriptorSets           vkUpdateDescriptorSets;
    pfn_vkCreateCommandPool              vkCreateCommandPool;
    pfn_vkDestroyCommandPool             vkDestroyCommandPool;
    pfn_vkAllocateCommandBuffers         vkAllocateCommandBuffers;
    pfn_vkBeginCommandBuffer             vkBeginCommandBuffer;
    pfn_vkEndCommandBuffer               vkEndCommandBuffer;
    pfn_vkCmdBindPipeline                vkCmdBindPipeline;
    pfn_vkCmdBindDescriptorSets          vkCmdBindDescriptorSets;
    pfn_vkCmdDispatch                    vkCmdDispatch;
    pfn_vkQueueSubmit                    vkQueueSubmit;
    pfn_vkQueueWaitIdle                  vkQueueWaitIdle;
    pfn_vkCreateBuffer                   vkCreateBuffer;
    pfn_vkDestroyBuffer                  vkDestroyBuffer;
    pfn_vkGetBufferMemoryRequirements    vkGetBufferMemoryRequirements;
    pfn_vkAllocateMemory                 vkAllocateMemory;
    pfn_vkFreeMemory                     vkFreeMemory;
    pfn_vkBindBufferMemory               vkBindBufferMemory;
    pfn_vkMapMemory                      vkMapMemory;
    pfn_vkUnmapMemory                    vkUnmapMemory;
    pfn_vkCreateFence                    vkCreateFence;
    pfn_vkDestroyFence                   vkDestroyFence;
    pfn_vkWaitForFences                  vkWaitForFences;
    pfn_vkResetFences                    vkResetFences;
    pfn_vkResetCommandBuffer             vkResetCommandBuffer;
} mn_vulkan_fns_t;

/* -----------------------------------------------------------------------
 * 5. GPU Context
 *
 * Holds loaded library handles, function pointers, and initialized
 * device state for both CUDA and Vulkan. One context per process.
 * ----------------------------------------------------------------------- */

/** CUDA runtime state. */
typedef struct mn_cuda_ctx {
    void            *lib_handle;    /* dlopen handle / HMODULE              */
    mn_cuda_fns_t    fn;            /* loaded function pointers             */
    CUdevice         device;        /* selected device ordinal              */
    CUcontext        context;       /* driver context                       */
    int              device_count;  /* number of CUDA devices               */
    int              initialized;   /* 1 if cuInit succeeded                */
    char             device_name[256];
    int64_t          device_memory; /* total device memory in bytes         */
} mn_cuda_ctx_t;

/** Vulkan runtime state. */
typedef struct mn_vulkan_ctx {
    void                *lib_handle;     /* dlopen handle / HMODULE         */
    mn_vulkan_fns_t      fn;             /* loaded function pointers        */
    VkInstance           instance;
    VkPhysicalDevice     physical_device;
    VkDevice             device;
    VkQueue              compute_queue;
    uint32_t             compute_queue_family;
    VkCommandPool        command_pool;
    int                  initialized;    /* 1 if pipeline is ready          */
    char                 device_name[256];
    MnVkPhysicalDeviceMemoryProperties mem_props;
} mn_vulkan_ctx_t;

/** Master GPU context — process-global singleton. */
typedef struct mn_gpu_ctx {
    mn_cuda_ctx_t    cuda;
    mn_vulkan_ctx_t  vulkan;
#ifdef __APPLE__
    /* Metal context — included inline to avoid header dependency.
     * Forward-declared; actual type is mn_metal_ctx_t from mapanare_metal.h. */
    void            *metal;         /* mn_metal_ctx_t* (heap-allocated)     */
    int              metal_initialized;
#endif
    int              prefer_cuda;   /* 1 = prefer CUDA over Vulkan         */
    int              initialized;   /* 1 after mapanare_gpu_init()         */
} mn_gpu_ctx_t;

/* -----------------------------------------------------------------------
 * 6. GPU Device Memory Handle
 *
 * Unified representation of a GPU memory allocation, regardless of backend.
 * ----------------------------------------------------------------------- */

typedef struct mn_gpu_buffer {
    mapanare_device_kind_t backend;
    size_t                 size_bytes;
    /* CUDA fields */
    CUdeviceptr            cu_ptr;
    /* Vulkan fields */
    VkBuffer               vk_buffer;
    VkDeviceMemory         vk_memory;
} mn_gpu_buffer_t;

/* -----------------------------------------------------------------------
 * 7. CUDA Kernel Handle
 * ----------------------------------------------------------------------- */

typedef struct mn_cuda_kernel {
    CUmodule   module;
    CUfunction function;
} mn_cuda_kernel_t;

/* -----------------------------------------------------------------------
 * 8. Vulkan Compute Pipeline Handle
 * ----------------------------------------------------------------------- */

typedef struct mn_vk_pipeline {
    VkShaderModule         shader_module;
    VkDescriptorSetLayout  descriptor_layout;
    VkPipelineLayout       pipeline_layout;
    VkPipeline             pipeline;
    VkDescriptorPool       descriptor_pool;
} mn_vk_pipeline_t;

/* -----------------------------------------------------------------------
 * 9. Public API — GPU Initialization
 * ----------------------------------------------------------------------- */

/** Initialize GPU subsystem. Attempts to load CUDA and Vulkan libraries.
 *  Returns 0 on success (at least one backend available), -1 if no GPU found.
 *  Safe to call multiple times — subsequent calls are no-ops. */
MN_GPU_EXPORT int mapanare_gpu_init(void);

/** Shut down GPU subsystem and release all resources. */
MN_GPU_EXPORT void mapanare_gpu_shutdown(void);

/** Get the global GPU context (read-only). Returns NULL if not initialized. */
MN_GPU_EXPORT const mn_gpu_ctx_t *mapanare_gpu_get_ctx(void);

/** Check if CUDA is available. Returns 1 if yes, 0 if no. */
MN_GPU_EXPORT int mapanare_gpu_has_cuda(void);

/** Check if Vulkan compute is available. Returns 1 if yes, 0 if no. */
MN_GPU_EXPORT int mapanare_gpu_has_vulkan(void);

/** Check if Metal compute is available (Apple platforms only). Returns 1 if yes, 0 if no. */
MN_GPU_EXPORT int mapanare_gpu_has_metal(void);

/* -----------------------------------------------------------------------
 * 10. Public API — GPU Memory Management
 * ----------------------------------------------------------------------- */

/** Allocate device memory on the specified backend.
 *  Returns NULL on failure. Caller must free with mapanare_gpu_buffer_free(). */
MN_GPU_EXPORT mn_gpu_buffer_t *mapanare_gpu_buffer_alloc(
    mapanare_device_kind_t backend, size_t size_bytes);

/** Free a GPU buffer. */
MN_GPU_EXPORT void mapanare_gpu_buffer_free(mn_gpu_buffer_t *buf);

/** Copy host data to GPU buffer. Returns 0 on success, -1 on error. */
MN_GPU_EXPORT int mapanare_gpu_buffer_upload(
    mn_gpu_buffer_t *dst, const void *src, size_t size_bytes);

/** Copy GPU buffer data to host. Returns 0 on success, -1 on error. */
MN_GPU_EXPORT int mapanare_gpu_buffer_download(
    void *dst, const mn_gpu_buffer_t *src, size_t size_bytes);

/* -----------------------------------------------------------------------
 * 11. Public API — CUDA Kernel Launch
 * ----------------------------------------------------------------------- */

/** Load a CUDA kernel from PTX source. name is the kernel function name.
 *  Returns NULL on failure. Caller must free with mapanare_cuda_kernel_free(). */
MN_GPU_EXPORT mn_cuda_kernel_t *mapanare_cuda_kernel_load(
    const char *ptx_source, const char *name);

/** Free a loaded CUDA kernel. */
MN_GPU_EXPORT void mapanare_cuda_kernel_free(mn_cuda_kernel_t *kernel);

/** Launch a CUDA kernel.
 *  grid/block dimensions, shared memory size, kernel parameters.
 *  Returns 0 on success, -1 on error. */
MN_GPU_EXPORT int mapanare_cuda_kernel_launch(
    mn_cuda_kernel_t *kernel,
    unsigned int grid_x, unsigned int grid_y, unsigned int grid_z,
    unsigned int block_x, unsigned int block_y, unsigned int block_z,
    unsigned int shared_mem,
    void **params);

/** Synchronize CUDA context (wait for all kernels to finish).
 *  Returns 0 on success, -1 on error. */
MN_GPU_EXPORT int mapanare_cuda_synchronize(void);

/* -----------------------------------------------------------------------
 * 12. Public API — Vulkan Compute Pipeline
 * ----------------------------------------------------------------------- */

/** Create a Vulkan compute pipeline from SPIR-V bytecode.
 *  num_storage_buffers specifies how many storage buffer bindings are needed.
 *  Returns NULL on failure. */
MN_GPU_EXPORT mn_vk_pipeline_t *mapanare_vk_pipeline_create(
    const uint32_t *spirv_code, size_t spirv_size_bytes,
    uint32_t num_storage_buffers);

/** Free a Vulkan compute pipeline and all associated resources. */
MN_GPU_EXPORT void mapanare_vk_pipeline_free(mn_vk_pipeline_t *pipeline);

/** Dispatch a Vulkan compute shader.
 *  buffers/num_buffers bind storage buffers to the pipeline.
 *  group_count_x/y/z specify workgroup counts.
 *  Returns 0 on success, -1 on error. */
MN_GPU_EXPORT int mapanare_vk_dispatch(
    mn_vk_pipeline_t *pipeline,
    mn_gpu_buffer_t **buffers, uint32_t num_buffers,
    uint32_t group_count_x, uint32_t group_count_y, uint32_t group_count_z);

/* -----------------------------------------------------------------------
 * 13. Public API — GPU Tensor Operations (CUDA)
 * ----------------------------------------------------------------------- */

/** Element-wise tensor add on CUDA. Returns new CPU tensor with result.
 *  Falls back to CPU if CUDA unavailable. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_gpu_tensor_add(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor subtract on CUDA. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_gpu_tensor_sub(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor multiply on CUDA. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_gpu_tensor_mul(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor divide on CUDA. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_gpu_tensor_div(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Matrix multiply on CUDA: (M,K) @ (K,N) -> (M,N). */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_gpu_tensor_matmul(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/* -----------------------------------------------------------------------
 * 14. Public API — GPU Tensor Operations (Vulkan)
 * ----------------------------------------------------------------------- */

/** Element-wise tensor add on Vulkan. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_vk_tensor_add(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor subtract on Vulkan. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_vk_tensor_sub(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor multiply on Vulkan. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_vk_tensor_mul(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor divide on Vulkan. */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_vk_tensor_div(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Matrix multiply on Vulkan: (M,K) @ (K,N) -> (M,N). */
MN_GPU_EXPORT mapanare_tensor_t *mapanare_vk_tensor_matmul(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

#endif /* MAPANARE_GPU_H */
