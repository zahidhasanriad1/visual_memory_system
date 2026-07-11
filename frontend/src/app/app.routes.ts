import { Routes } from '@angular/router';

import { AppShellComponent } from './layout/app-shell/app-shell.component';

import { LoginPageComponent } from './features/auth/pages/login/login-page';
import { RegisterPageComponent } from './features/auth/pages/register/register-page';

import { DashboardComponent } from './features/dashboard/pages/dashboard/dashboard.component';
import { ImageFeaturesPageComponent } from './features/image-features/pages/image-features-page';
import { VideoMemoryComponent } from './features/video-memory/pages/video-memory/video-memory.component';
import { CloudAiPageComponent } from './features/cloud-ai/pages/cloud-ai-page';
import { AnnotationWorkspaceComponent } from './features/annotation/pages/annotation-workspace/annotation-workspace.component';
import { AdaptiveReviewComponent } from './features/adaptive-learning/pages/adaptive-review/adaptive-review.component';
import { TrainingOrchestratorComponent } from './features/training/pages/training-orchestrator/training-orchestrator.component';
import { ModelRegistryComponent } from './features/model-registry/pages/model-registry/model-registry.component';
import { CustomTrainingComponent } from './features/training/pages/custom-training/custom-training.component';

import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginPageComponent,
  },
  {
    path: 'register',
    component: RegisterPageComponent,
  },
  {
    path: '',
    component: AppShellComponent,
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
      {
        path: 'dashboard',
        component: DashboardComponent,
        data: { roles: ['admin', 'annotator', 'user', 'viewer'] },
      },
      {
        path: 'image-features',
        component: ImageFeaturesPageComponent,
        data: { roles: ['admin', 'annotator', 'user', 'viewer'] },
      },
      {
        path: 'video-memory',
        component: VideoMemoryComponent,
        data: { roles: ['admin', 'user'] },
      },
      {
        path: 'cloud-ai',
        component: CloudAiPageComponent,
        data: { roles: ['admin', 'user'] },
      },
      {
        path: 'annotation',
        component: AnnotationWorkspaceComponent,
        data: { roles: ['admin', 'annotator', 'user'] },
      },
      {
        path: 'adaptive-learning',
        component: AdaptiveReviewComponent,
        data: { roles: ['admin', 'annotator', 'user'] },
      },
      {
        path: 'approval',
        component: AdaptiveReviewComponent,
        data: { roles: ['admin', 'annotator', 'user'] },
      },
      {
        path: 'custom-training',
        component: CustomTrainingComponent,
        data: { roles: ['admin', 'user'] },
      },
      {
        path: 'training',
        component: TrainingOrchestratorComponent,
        data: { roles: ['admin'] },
      },
      {
        path: 'model-registry',
        component: ModelRegistryComponent,
        data: { roles: ['admin'] },
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
