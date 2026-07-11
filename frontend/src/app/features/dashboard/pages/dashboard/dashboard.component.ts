import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { catchError, finalize, of, retry, take } from 'rxjs';

import { AuthApiService } from '../../../../core/services/auth-api.service';
import { ImageFeatureApiService } from '../../../../core/services/image-feature-api.service';
import { ImageFeatureDashboardItem } from '../../../../core/types/image-features/image-feature.types';
import {
  DashboardCard,
  DashboardModule,
  ImageDashboardState,
  ImageHistoryFilter,
  ImageHistoryFilterOption,
} from './dashboard.types';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly imageFeatureApi = inject(ImageFeatureApiService);

  imageDashboard: ImageDashboardState | null = null;
  imageDashboardItems: ImageFeatureDashboardItem[] = [];
  isLoadingImageDashboard = false;
  imageDashboardError = '';
  activeImageFilter: ImageHistoryFilter = 'all';

  readonly imageFilters: ImageHistoryFilterOption[] = [
    { label: 'All', value: 'all' },
    { label: 'Tested', value: 'source' },
    { label: 'Detected', value: 'detection' },
    { label: 'Crops', value: 'crop' },
    { label: 'Memory', value: 'memory' },
  ];

  readonly cards: DashboardCard[] = [
    {
      title: 'Image Intelligence',
      value: '5 APIs',
      roles: ['admin', 'annotator', 'user', 'viewer'],
    },
    {
      title: 'Video Memory',
      value: 'Timeline',
      roles: ['admin', 'user'],
    },
    {
      title: 'AI Agents',
      value: 'Hybrid',
      roles: ['admin', 'user'],
    },
    {
      title: 'Admin Control',
      value: 'Safe',
      roles: ['admin'],
    },
  ];

  readonly modules: DashboardModule[] = [
    {
      path: '/image-features',
      title: 'Image Feature Pipeline',
      status: 'Connected',
      roles: ['admin', 'annotator', 'user', 'viewer'],
    },
    {
      path: '/video-memory',
      title: 'Video Memory',
      status: 'Active',
      roles: ['admin', 'user'],
    },
    {
      path: '/cloud-ai',
      title: 'Cloud AI + Hugging Face Intelligence',
      status: 'Active',
      roles: ['admin', 'user'],
    },
    {
      path: '/annotation',
      title: 'Annotation Workspace',
      status: 'Role gated',
      roles: ['admin', 'annotator', 'user'],
    },
    {
      path: '/approval',
      title: 'Approval Review',
      status: 'Active',
      roles: ['admin', 'annotator', 'user'],
    },
    {
      path: '/custom-training',
      title: 'Custom Object Training',
      status: 'Annotation → model',
      roles: ['admin', 'user'],
    },
    {
      path: '/training',
      title: 'Training Orchestrator',
      status: 'Admin only',
      roles: ['admin'],
    },
    {
      path: '/model-registry',
      title: 'Model Registry',
      status: 'Admin only',
      roles: ['admin'],
    },
  ];

  get visibleCards(): DashboardCard[] {
    return this.cards.filter((card) => this.authApi.hasAnyRole(card.roles));
  }

  get visibleModules(): DashboardModule[] {
    return this.modules.filter((module) => this.authApi.hasAnyRole(module.roles));
  }

  get filteredImageDashboardItems(): ImageFeatureDashboardItem[] {
    if (this.activeImageFilter === 'all') {
      return this.imageDashboardItems;
    }

    return this.imageDashboardItems.filter((item) =>
      item.image_kinds.includes(this.activeImageFilter)
    );
  }

  ngOnInit(): void {
    this.loadDashboardImages();
  }

  loadDashboardImages(): void {
    this.isLoadingImageDashboard = true;
    this.imageDashboardError = '';

    this.imageFeatureApi
      .getDashboardImages(24)
      .pipe(
        take(1),
        retry({ count: 1, delay: 500 }),
        catchError((error) => {
          const message =
            error?.name === 'TimeoutError'
              ? 'Image dashboard request timed out. Check backend port 8000 and start frontend with npm start.'
              : error?.error?.message ||
                error?.message ||
                'Image dashboard request failed. Check backend port 8000 and the frontend proxy.';

          this.applyImageDashboardFailure(message);
          return of(null);
        }),
        finalize(() => {
          this.isLoadingImageDashboard = false;
        })
      )
      .subscribe({
        next: (response) => {
          if (!response) {
            return;
          }

          if (!response?.success || !response.data) {
            this.applyImageDashboardFailure(
              response?.message || 'Image dashboard response is invalid.'
            );
            return;
          }

          this.imageDashboard = response.data;
          this.imageDashboardItems = response.data.items ?? [];
        },
      });
  }

  filterCount(filter: ImageHistoryFilter): number {
    if (filter === 'all') {
      return this.imageDashboardItems.length;
    }

    return this.imageDashboardItems.filter((item) => item.image_kinds.includes(filter)).length;
  }

  private applyImageDashboardFailure(message: string): void {
    this.imageDashboard = null;
    this.imageDashboardItems = [];
    this.imageDashboardError = message;
  }
}
