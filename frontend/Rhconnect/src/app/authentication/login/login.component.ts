import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from 'src/app/services/auth/auth.service';
import { NgForm } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, HttpClientModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export default class LoginComponent {
  credentials = { email: '', password: '' };

  constructor(private authService: AuthService, private router: Router) {}

  login(form: NgForm) {
  if (form.invalid) {
    return; // stop si le formulaire est invalide
  }

  this.authService.login(this.credentials).subscribe({
    next: (response) => {
      console.log('Token:', response.token);
      localStorage.setItem('access_token', response.token);
      localStorage.setItem('refresh_token', response.refresh);
      localStorage.setItem('user_info', JSON.stringify(response.user));
      localStorage.setItem('user_role', response.user.role);
      localStorage.setItem('username', response.user.username);

      if (response.user.role === 'gestionnaire_rh' || response.user.role === 'recruteur') {
        this.router.navigate(['/admin/dashboard']);
      } else {
        this.router.navigate(['/']);
      }
    },
    error: (error) => {
      alert(error.error.message || 'Email ou mot de passe incorrect.');
    }
  });
}
}