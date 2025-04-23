import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AjoutOffreComponent } from './ajout-offre.component';

describe('AjoutOffreComponent', () => {
  let component: AjoutOffreComponent;
  let fixture: ComponentFixture<AjoutOffreComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AjoutOffreComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AjoutOffreComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
