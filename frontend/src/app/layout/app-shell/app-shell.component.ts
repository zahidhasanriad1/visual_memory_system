import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, TopbarComponent],
  template: `
    <div class="shell" [class.sidebar-open]="isSidebarOpen">
      <app-sidebar [isOpen]="isSidebarOpen" (navigate)="closeSidebar()" />
      <div class="backdrop" (click)="closeSidebar()"></div>

      <main>
        <app-topbar (menuClick)="toggleSidebar()" />
        <section class="page">
          <router-outlet />
        </section>
      </main>
    </div>
  `,
  styles: [
    `
      .shell {
        min-height: 100vh;
        display: grid;
        grid-template-columns: 252px minmax(0, 1fr);
        background: #edf3fb;
      }

      main {
        min-width: 0;
        min-height: 100vh;
        display: grid;
        grid-template-rows: auto 1fr;
      }

      .page {
        min-width: 0;
        min-height: calc(100vh - 56px);
        padding: 18px 20px;
      }

      .backdrop {
        display: none;
      }

      @media (max-width: 980px) {
        .shell {
          grid-template-columns: 1fr;
        }

        .backdrop {
          position: fixed;
          inset: 0;
          z-index: 30;
          display: block;
          pointer-events: none;
          background: rgba(15, 23, 42, 0);
          transition: background 160ms ease;
        }

        .sidebar-open .backdrop {
          pointer-events: auto;
          background: rgba(15, 23, 42, 0.42);
        }

        .page {
          padding: 14px;
        }
      }
    `,
  ],
})
export class AppShellComponent {
  isSidebarOpen = false;

  toggleSidebar(): void {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  closeSidebar(): void {
    this.isSidebarOpen = false;
  }
}
