import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmployeService } from 'src/app/services/employe/employe.service';

@Component({
  selector: 'app-employe-profil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './employe-profil.component.html',
  styleUrls: ['./employe-profil.component.scss']
})
export class EmployeProfilComponent implements OnInit {
  profil: any = null;
  isSaving = false;

  // Edition
  editMode = false;
  edit: any = {};
  avatarFile: File | null = null;
 
avatarPreview: string | null = null;

  constructor(private employeService: EmployeService) {}

  ngOnInit(): void {
    this.load();
  }

  private load() {
    this.employeService.getMonProfilEtSuivi().subscribe({
      next: (data: any) => {
        this.profil = data?.profil ?? data?.employe ?? {};
      },
      error: (e) => console.error(e)
    });
  }

  toggleEdit() {
    this.editMode = !this.editMode;
    if (this.editMode && this.profil) {
      // Pré-remplir le formulaire d’édition
      this.edit = {
        prenom: this.profil.prenom || '',
        nom: this.profil.nom || '',
        numero_tel: this.profil.numero_tel || '',
        adresse: this.profil.adresse || '',
        date_naissance: this.profil.date_naissance || ''
      };
      this.avatarFile = null;
    }
  }

 onFile(ev: Event) {
  const input = ev.target as HTMLInputElement;
  if (input.files && input.files.length) {
    this.avatarFile = input.files[0];

    // ✅ Générer un aperçu
    const reader = new FileReader();
    reader.onload = () => {
      this.avatarPreview = reader.result as string;
    };
    reader.readAsDataURL(this.avatarFile);
  }
}

  save() {
     if (this.isSaving) return;
  this.isSaving = true;
  // 1) payload texte uniquement (PAS de fichier ici)
  const payload: any = {};
  Object.entries(this.edit).forEach(([k, v]) => {
    if (v !== null && v !== undefined && k !== 'avatar') payload[k] = v;
  });

this.employeService.updateProfilEmploye(payload).subscribe({
    next: (updated: any) => {
      this.profil = { ...this.profil, ...(updated?.profil ?? payload) };

      const afterAll = () => { this.afterSaveOk(); this.isSaving = false; };

      if (this.avatarFile) {
        // (optionnel) petit contrôle
        if (!this.avatarFile.type.startsWith('image/')) {
          this.afterSaveErr('Format de fichier non valide'); this.isSaving = false; return;
        }

        this.employeService.uploadAvatar(this.avatarFile).subscribe({
          next: (res: any) => {
            const url = (res?.avatar || '').trim();
            const bust = url ? `${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}` : url;
            this.profil.avatar = bust;
            this.employeService.avatarChanged$.next(bust); // maj navbar
            afterAll();
          },
          error: (e) => { this.afterSaveErr(e); this.isSaving = false; }
        });
      } else {
        afterAll();
      }
    },
    error: (e) => { this.afterSaveErr(e); this.isSaving = false; }
  });
}

private afterSaveOk() {
  this.avatarPreview = null;
  this.editMode = false;
  // toast/alert si tu veux
}

private afterSaveErr(e: any) {
  console.error(e);
  alert('Échec de la mise à jour.');
}
}
