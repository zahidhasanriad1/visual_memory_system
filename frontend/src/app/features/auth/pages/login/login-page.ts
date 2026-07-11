import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthApiService } from '../../../../core/services/auth-api.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login-page.html',
  styleUrl: './login-page.scss',
})
export class LoginPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);

  isLoading = false;
  errorMessage: string | null = null;

  readonly form = this.fb.nonNullable.group({
    email: '',
    password: '',
  });

  submit(): void {
    const email = this.form.controls.email.value.trim();
    const password = this.form.controls.password.value;

    if (!email || !password) {
      this.errorMessage = 'Email and password are required.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    this.authApi.loginForm(email, password).subscribe({
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
          'Login failed.';
      },
    });
  }
}