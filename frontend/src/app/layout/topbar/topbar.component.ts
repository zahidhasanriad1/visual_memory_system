import { Component, EventEmitter, Output, inject } from '@angular/core';
import { AuthApiService } from '../../core/services/auth-api.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  template: `
    <header>
      <button class="menu-button" type="button" (click)="menuClick.emit()" aria-label="Open navigation">
        <span></span>
        <span></span>
        <span></span>
      </button>

      <div class="title">
        <strong>VMS-X Console</strong>
      </div>

      <div class="account">
        <div>
          <strong>{{ userName }}</strong>
          <span>{{ userRole }}</span>
        </div>
        <button type="button" (click)="logout()">Logout</button>
      </div>
    </header>
  `,
  styles: [
    `
      header {
        position: sticky;
        top: 0;
        z-index: 20;
        height: 56px;
        display: flex;
        align-items: center;
        gap: 18px;
        justify-content: space-between;
        padding: 0 20px;
        border-bottom: 1px solid #dbe4f0;
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(14px);
      }

      .menu-button {
        display: none;
        width: 38px;
        height: 38px;
        border: 1px solid #dbe4f0;
        border-radius: 8px;
        background: #ffffff;
        place-items: center;
        padding: 10px;
        cursor: pointer;
      }

      .menu-button span {
        display: block;
        width: 18px;
        height: 2px;
        margin: 3px auto;
        background: #0f172a;
      }

      .title {
        min-width: 0;
        display: flex;
        flex-direction: column;
      }

      .title strong {
        color: #0f172a;
        font-size: 16px;
        font-weight: 900;
      }

      .account {
        display: flex;
        align-items: center;
        gap: 14px;
      }

      .account div {
        display: flex;
        flex-direction: column;
        text-align: right;
      }

      .account strong {
        color: #0f172a;
        font-size: 14px;
        font-weight: 900;
      }

      .account span {
        margin-top: 2px;
        color: #64748b;
        font-size: 12px;
        font-weight: 800;
        text-transform: capitalize;
      }

      .account button {
        height: 38px;
        border: none;
        border-radius: 8px;
        background: #dc2626;
        color: #ffffff;
        padding: 0 14px;
        font-weight: 900;
        cursor: pointer;
      }

      @media (max-width: 980px) {
        header {
          padding: 0 16px;
        }

        .menu-button {
          display: block;
          flex: 0 0 auto;
        }
      }

      @media (max-width: 680px) {
        .account div {
          display: none;
        }

        .title strong {
          font-size: 15px;
        }
      }
    `,
  ],
})
export class TopbarComponent {
  private readonly authApi = inject(AuthApiService);

  @Output() menuClick = new EventEmitter<void>();

  get userName(): string {
    return this.authApi.getStoredUser()?.full_name || 'VMS User';
  }

  get userRole(): string {
    return this.authApi.getStoredRole();
  }

  logout(): void {
    this.authApi.logout();
  }
}
