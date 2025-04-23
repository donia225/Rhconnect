import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from 'src/app/services/auth/auth.service';

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

  login() {
    this.authService.login(this.credentials).subscribe({
      next: (response) => {
        console.log('Token:', response.token);
        localStorage.setItem('access_token', response.token);
        localStorage.setItem('refresh_token', response.refresh);
    

        localStorage.setItem('user_info', JSON.stringify(response.user));

        localStorage.setItem('user_role', response.user.role); // ✅ Store user role
        localStorage.setItem('username', response.user.username);
  
        // ✅ Redirect based on user role
        if (response.user.role === 'gestionnaire_rh' || response.user.role === 'recruteur') {
          this.router.navigate(['/admin/dashboard']); // ✅ Redirect to dashboard for HR & Recruiter
        } else {
          this.router.navigate(['/']); // ✅ Default route (Accueil)
        }
      },
      error: (error) => {
        alert(error.error.message || 'Email ou mot de passe incorrect.');
      }
    });
  }
}  
