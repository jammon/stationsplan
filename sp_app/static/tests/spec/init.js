var persons_init = [
  { name: 'Anton', id: 'A', functions: ['A', 'B', 'N', 'O']},
  { name: 'Berta', id: 'B', functions: ['A', 'B', 'N', 'O']},
  { name: 'Conny', id: 'C', functions: ['A', 'B']}, // no nightshifts
  { name: 'Other', id: 'Other', functions: ['A', 'B'], anonymous: true}
];
var wards_init = [
  { name: 'Ward A', shortname: 'A', min: 1, max: 2 },
  { name: 'Ward B', shortname: 'B', min: 2, max: 2 },
  { name: 'Nightshift', shortname: 'N', min: 0, max: 1, nightshift: true, 
    callshift: true, everyday: true, weight: 2, ward_type: 'Callshifts' },
  { name: 'Leave', shortname: 'L', min: 0, max: 10, on_leave: true },
  { name: 'Free days', shortname: 'F', min: 0, max: 10, freedays: true },
  { name: 'Visite', shortname: 'V', min: 0, max: 10, weekdays: '6', 
    callshift: true, weight: 1 },
  { name: 'One day task', shortname: 'O', min: 0, max: 10, 
    callshift: true, weight: 3, ward_type: 'Callshifts' },
  { name: 'Special', shortname: 'S', min: 0, max: 10,
    after_this: 'S,A' },
];
var different_days = [
  ['V', '20150808', '-'],
  ['V', '20150809', '+'],
];
function init_hospital() {
    models.initialize_wards(wards_init, different_days);
    models.persons.reset(persons_init);
}

