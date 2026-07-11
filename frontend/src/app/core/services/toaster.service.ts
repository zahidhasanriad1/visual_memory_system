import { Injectable, signal } from '@angular/core';

export interface ToastMessage { id: number; type: 'success' | 'error' | 'info'; message: string; }

@Injectable({ providedIn: 'root' })
export class ToasterService {
  readonly messages = signal<ToastMessage[]>([]);
  private nextId = 1;

  show(type: ToastMessage['type'], message: string): void {
    const item = { id: this.nextId++, type, message };
    this.messages.update((items) => [...items, item]);
    window.setTimeout(() => this.remove(item.id), 4000);
  }
  remove(id: number): void { this.messages.update((items) => items.filter((item) => item.id !== id)); }
}
