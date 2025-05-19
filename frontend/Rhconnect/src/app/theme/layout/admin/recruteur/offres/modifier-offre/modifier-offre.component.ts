import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { OffreService } from 'src/app/services/offre/offre.service';
import { SharedModule } from 'src/app/theme/shared/shared.module';

@Component({
  selector: 'app-modifier-offre',
  imports: [FormsModule,SharedModule],
  templateUrl: './modifier-offre.component.html',
  styleUrls: ['./modifier-offre.component.scss']
})
export class ModifierOffreComponent implements OnInit {
  offreId!: number;
  offre = {
    titre: '',
    type_poste: '',
    experience: '',
    niveau_etude: '',
    disponibilite: '',
    langues: '',
    description: '',
    salaire: null,
    competences:''
  };

  constructor(
    private route: ActivatedRoute,
    private offreService: OffreService,
    private router: Router, private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    this.offreId = Number(this.route.snapshot.paramMap.get('id'));
    this.offreService.getAllOffres().subscribe((res) => {
      const current = res.find((o: any) => o.id === this.offreId);
      if (current) this.offre = current;
    });
  }

  onSubmit(): void {
    const user = JSON.parse(localStorage.getItem('user_info') || '{}');
    const data = {
      ...this.offre,
      recruteur: user.id
    };

    this.offreService.modifierOffre(this.offreId, data).subscribe({
      next: () => {
        this.toastr.success("Offre modifiée avec succès !");
        this.router.navigate(['/admin/offres/liste']);
      },
      error: () => {
        alert('Erreur lors de la modification');
      }
    });
  }
    annuler() {
  this.router.navigate(['/admin/offres/liste']); // redirection vers la liste des offres
}
}
