/**
 * Barrel re-export — 统一入口
 * 组件通过 `import { authApi, fileApi, chatApi } from '@/api/auto'` 引用
 */
export { authApi } from './auth';
export { fileApi } from './file';
export { chatApi } from './chat';

// 向下兼容：旧代码 import { uploadApi } from './auto'
export { fileApi as uploadApi } from './file';

export { resumeApi } from './resume';

// 类型也统一导出
export type * from './types';