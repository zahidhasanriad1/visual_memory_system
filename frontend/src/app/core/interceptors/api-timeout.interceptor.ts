import { HttpInterceptorFn } from '@angular/common/http';
import { timeout } from 'rxjs';

const DEFAULT_GET_TIMEOUT_MS = 15000;
const DEFAULT_NON_UPLOAD_TIMEOUT_MS = 30000;

export const apiTimeoutInterceptor: HttpInterceptorFn = (request, next) => {
  if (request.method.toUpperCase() !== 'GET') {
    const isFileUpload =
      typeof FormData !== 'undefined' && request.body instanceof FormData;

    if (isFileUpload) {
      return next(request);
    }

    return next(request).pipe(timeout({ first: DEFAULT_NON_UPLOAD_TIMEOUT_MS }));
  }

  return next(request).pipe(timeout({ first: DEFAULT_GET_TIMEOUT_MS }));
};
