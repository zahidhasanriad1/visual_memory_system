import { Component, inject } from '@angular/core';
import { ToasterService } from '../../../core/services/toaster.service';

@Component({
  selector: 'app-toaster',
  standalone: true,
  template: `
    <section class="toaster">
      @for (toast of toaster.messages(); track toast.id) {
        <button class="toast" [class.success]="toast.type==='success'" [class.error]="toast.type==='error'" (click)="toaster.remove(toast.id)">{{ toast.message }}</button>
      }
    </section>
  `,
  styles: [`
    .toaster{position:fixed;right:20px;top:20px;display:grid;gap:10px;z-index:9999}.toast{border:0;border-radius:14px;padding:14px 16px;color:white;background:#2563eb;box-shadow:0 14px 40px #0f172a33}.success{background:#16a34a}.error{background:#dc2626}
  `]
})
export class ToasterComponent { readonly toaster = inject(ToasterService); }
