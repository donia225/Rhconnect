import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GestionCarriereComponent } from './gestion-carriere.component';

describe('GestionCarriereComponent', () => {
  let component: GestionCarriereComponent;
  let fixture: ComponentFixture<GestionCarriereComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GestionCarriereComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GestionCarriereComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
