import { CanActivateChildFn, CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthApiService } from '../services/auth-api.service';

export const authGuard: CanActivateFn | CanActivateChildFn = (route) => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isLoggedIn()) {
    return router.createUrlTree(['/login']);
  }

  const roles = route.data?.['roles'] as string[] | undefined;

  if (!authApi.hasAnyRole(roles)) {
    return router.createUrlTree(['/dashboard']);
  }

  return true;
};
