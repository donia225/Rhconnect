import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
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
      niveau_experience: [''],
      numero_tel: [''],
      adresse: [''],
      cv: [null],
      projects_count:['']
    });

    this.loadProfil();
  }

  loadProfil() {
    this.profilService.getProfil().subscribe(data => {
      this.profilForm.patchValue(data);
    });
  }

  onSubmit() {
    if (this.profilForm.valid) {
      this.profilService.updateProfil(this.profilForm.value).subscribe(() => {
        alert("Profil mis à jour avec succès !");
        const pendingOffreId = localStorage.getItem('pending_offre_id');
if (pendingOffreId) {
  localStorage.removeItem('pending_offre_id');
  this.router.navigate(['/offres'], { queryParams: { offreId: pendingOffreId } });
}
      });
    }
  }
}
