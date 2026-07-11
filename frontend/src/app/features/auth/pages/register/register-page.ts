import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthApiService } from '../../../../core/services/auth-api.service';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register-page.html',
  styleUrl: './register-page.scss',
})
export class RegisterPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);

  isLoading = false;
  errorMessage: string | null = null;

  readonly form = this.fb.nonNullable.group({
    fullName: '',
    email: '',
    password: '',
    role: 'user',
  });

  submit(): void {
    const fullName = this.form.controls.fullName.value.trim();
    const email = this.form.controls.email.value.trim();
    const password = this.form.controls.password.value;
    const role = this.form.controls.role.value;

    if (!fullName || !email || !password) {
      this.errorMessage = 'All fields are required.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    this.authApi
      .register({
        full_name: fullName,
        email,
        password,
        role,
      })
      .subscribe({
        next: (response) => {
          this.isLoading = false;

          if (!response.success) {
            this.errorMessage = response.message;
            return;
          }

          this.router.navigateByUrl('/dashboard');
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage =
            error?.error?.detail?.message ||
            error?.error?.message ||
            error?.message ||
            'Registration failed.';
        },
      });
  }
}
