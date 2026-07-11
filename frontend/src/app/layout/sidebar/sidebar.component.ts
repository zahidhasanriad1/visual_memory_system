import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthApiService } from '../../core/services/auth-api.service';

interface NavItem {
  path: string;
  label: string;
  roles: string[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <aside [class.open]="isOpen">
      <div class="brand">
        <strong>VMS-X</strong>
      </div>

      <nav>
        @for (item of visibleItems; track item.path) {
          <a
            [routerLink]="item.path"
            routerLinkActive="active"
            [routerLinkActiveOptions]="{ exact: true }"
            (click)="navigate.emit()"
          >
            <span>{{ item.label }}</span>
          </a>
        }
      </nav>

      <div class="role-card">
        <strong>{{ displayRole }}</strong>
      </div>
    </aside>
  `,
  styles: [
    `
      aside {
        position: sticky;
        top: 0;
        z-index: 40;
        height: 100vh;
        display: grid;
        grid-template-rows: auto 1fr auto;
        gap: 14px;
        padding: 18px 14px;
        background: #0b1220;
        color: #ffffff;
        border-right: 1px solid rgba(148, 163, 184, 0.18);
      }

      .brand {
        padding: 8px 10px 18px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.18);
      }

      .brand strong {
        display: block;
        font-size: 26px;
        line-height: 1;
        font-weight: 950;
        letter-spacing: 0;
      }

      nav {
        min-height: 0;
        display: grid;
        align-content: start;
        gap: 8px;
        overflow: auto;
        padding-right: 2px;
      }

      a {
        display: flex;
        align-items: center;
        min-height: 44px;
        padding: 0 14px;
        border-radius: 8px;
        color: #cbd5e1;
        border: 1px solid transparent;
        text-decoration: none;
        transition:
          background 140ms ease,
          color 140ms ease,
          border-color 140ms ease;
      }

      a span {
        font-size: 13px;
        font-weight: 850;
      }

      a:hover,
      a.active {
        background: #1d4ed8;
        border-color: rgba(191, 219, 254, 0.32);
        color: #ffffff;
      }


      .role-card {
        padding: 10px 12px;
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.2);
      }

      .role-card strong {
        display: block;
        font-size: 14px;
        text-transform: capitalize;
      }

      @media (max-width: 980px) {
        aside {
          position: fixed;
          inset: 0 auto 0 0;
          width: min(86vw, 320px);
          transform: translateX(-102%);
          transition: transform 180ms ease;
          box-shadow: 26px 0 60px rgba(15, 23, 42, 0.32);
        }

        aside.open {
          transform: translateX(0);
        }
      }
    `,
  ],
})
export class SidebarComponent {
  private readonly authApi = inject(AuthApiService);

  @Input() isOpen = false;
  @Output() navigate = new EventEmitter<void>();

  readonly items: NavItem[] = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      roles: ['admin', 'annotator', 'user', 'viewer'],
    },
    {
      path: '/image-features',
      label: 'Image Feature Pipeline',
      roles: ['admin', 'annotator', 'user', 'viewer'],
    },
    {
      path: '/video-memory',
      label: 'Video Memory',
      roles: ['admin', 'user'],
    },
    {
      path: '/cloud-ai',
      label: 'Cloud AI + Hugging Face',
      roles: ['admin', 'user'],
    },
    {
      path: '/annotation',
      label: 'Annotation',
      roles: ['admin', 'annotator', 'user'],
    },
    {
      path: '/approval',
      label: 'Approval Review',
      roles: ['admin', 'annotator', 'user'],
    },
    {
      path: '/custom-training',
      label: 'Custom Training',
      roles: ['admin', 'user'],
    },
    {
      path: '/training',
      label: 'Training Orchestrator',
      roles: ['admin'],
    },
    {
      path: '/model-registry',
      label: 'Model Registry',
      roles: ['admin'],
    },
  ];

  get visibleItems(): NavItem[] {
    return this.items.filter((item) => this.authApi.hasAnyRole(item.roles));
  }

  get displayRole(): string {
    return this.authApi.getStoredRole();
  }
}
