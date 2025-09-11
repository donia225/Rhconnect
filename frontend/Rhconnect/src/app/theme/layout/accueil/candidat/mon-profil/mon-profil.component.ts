import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ProfilService } from 'src/app/services/profil/profil.service';


@Component({
  selector: 'app-mon-profil-cv',
  imports:[RouterModule, CommonModule, ReactiveFormsModule],
  templateUrl: './mon-profil.component.html',
  styleUrls: ['./mon-profil.component.scss']
})
export class MonProfilComponent implements OnInit {
  profilForm!: FormGroup;
  selectedFile!: File;

  constructor(private fb: FormBuilder, private profilService: ProfilService, private router:Router) {}

  ngOnInit(): void {
    this.profilForm = this.fb.group({
      nom: [{ value: '', disabled: true }],
      prenom: [{ value: '', disabled: true }],
      date_naissance: [''],
      niveau_etude: [''],
      numero_tel: ['', [Validators.required, tunisianPhoneValidator()]],
      adresse: ['', [
        Validators.required,
        Validators.pattern(/^(?=.*[A-Za-zÀ-ÿ])(?=.*\d)?[A-Za-zÀ-ÿ0-9\s'.,\-\/]{5,100}$/)
      ]],
      cv: [null],
    
    });

    this.loadProfil();
  }

  loadProfil() {
    this.profilService.getProfil().subscribe(data => {
      this.profilForm.patchValue(data);
    });
  }

 onSubmit() {
  if (this.profilForm.invalid) return;

  this.profilService.updateProfil(this.profilForm.value).subscribe({
    next: () => {
      alert('Profil mis à jour avec succès !');

      const pendingOffreId = localStorage.getItem('pending_offre_id');
      localStorage.removeItem('pending_offre_id');

      if (pendingOffreId) {
        this.router.navigate(['/offres'], { queryParams: { offreId: pendingOffreId } });
      } else {
        this.router.navigate(['/']);
      }
    },
    error: (err) => console.error(err)
  });
}

  keepDigitsOnly(ctrlName: string) {
    const c = this.profilForm.get(ctrlName);
    if (!c) return;
    const digits = String(c.value ?? '').replace(/\D+/g, '').slice(0, 8);
    if (digits !== c.value) c.setValue(digits, { emitEvent: false });
  }
}
export function tunisianPhoneValidator(): ValidatorFn {
  // Règles générales : 8 chiffres
  // Mobiles :
  //  - Ooredoo: 20–29
  //  - Orange:  50–59
  //  - TT Mobile: 90–99
  // Fixes (classiques) : 70–79 (tu peux élargir si nécessaire)
  const allowedPrefixes = [
    // Ooredoo
    '20','21','22','23','24','25','26','27','28','29',
    // Orange
    '50','51','52','53','54','55','56','57','58','59',
    // TT Mobile
    '90','91','92','93','94','95','96','97','98','99',
    // Fixes (exemples)
    '70','71','72','73','74','75','76','77','78','79'
  ];

  return (control: AbstractControl): ValidationErrors | null => {
    const v: string = (control.value ?? '').toString();
    if (!/^\d{8}$/.test(v)) return { tnPhone: true };
    const prefix = v.slice(0, 2);
    if (!allowedPrefixes.includes(prefix)) return { tnPhone: true };
    return null;
  };
}
