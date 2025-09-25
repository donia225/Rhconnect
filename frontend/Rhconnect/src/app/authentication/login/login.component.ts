import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
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
export default class LoginComponent implements OnInit {
  credentials = { email: '', password: '' };
  rememberMe: boolean = false;

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    // Pré-remplir l'email si mémorisé
    const savedEmail = localStorage.getItem('rememberedEmail');
    if (savedEmail) {
      this.credentials.email = savedEmail;
      this.rememberMe = true;
    }
  }

  login(form: NgForm) {
  if (form.invalid) {
    return;
  }

  this.authService.login(this.credentials).subscribe({
    next: (response) => {
      const storage = this.rememberMe ? localStorage : sessionStorage;
      
      console.log('Token:', response.token);
      localStorage.setItem('access_token', response.token);
      localStorage.setItem('refresh_token', response.refresh);
      localStorage.setItem('user_info', JSON.stringify(response.user));
      localStorage.setItem('user_role', response.user.role);
      localStorage.setItem('username', response.user.username);

       if (this.rememberMe) {
          localStorage.setItem('rememberedEmail', this.credentials.email);
        } else {
          localStorage.removeItem('rememberedEmail');
        }


        if (response.user.role === 'gestionnaire_rh' || response.user.role === 'recruteur') {
          this.router.navigate(['/admin/dashboard']);
        } else if (response.user.role === 'employe') {
            this.router.navigate(['/employe/dashboard']);
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