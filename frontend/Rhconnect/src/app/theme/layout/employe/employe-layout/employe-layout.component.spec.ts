import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmployeLayoutComponent } from './employe-layout.component';

describe('EmployeLayoutComponent', () => {
  let component: EmployeLayoutComponent;
  let fixture: ComponentFixture<EmployeLayoutComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmployeLayoutComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EmployeLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
