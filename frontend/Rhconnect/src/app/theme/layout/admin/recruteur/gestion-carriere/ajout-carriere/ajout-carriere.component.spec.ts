import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AjoutCarriereComponent } from './ajout-carriere.component';

describe('AjoutCarriereComponent', () => {
  let component: AjoutCarriereComponent;
  let fixture: ComponentFixture<AjoutCarriereComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AjoutCarriereComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AjoutCarriereComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
