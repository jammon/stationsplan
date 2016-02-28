var persons_init = [
  { name: 'Anton', id: 'A', functions: ['A', 'B']},
  { name: 'Berta', id: 'B', functions: ['A', 'B']},
];
var wards_init = [
  { name: 'Ward A', shortname: 'A', min: 1, max: 2, continued: true },
  { name: 'Ward B', shortname: 'B', min: 2, max: 2, continued: true },
  { name: 'Nightshift', shortname: 'N', min: 0, max: 1, nightshift: true, everyday: true },
  { name: 'Leave', shortname: 'L', min: 0, max: 10, on_leave: true, continued: true },
  { name: 'Free days', shortname: 'F', min: 0, max: 10, freedays: true, continued: true },
  { name: 'One day task', shortname: 'O', min: 0, max: 10, continued: false },
  { name: 'Special', shortname: 'S', min: 0, max: 10, continued: false, after_this: 'S,A' },
];
function init_hospital() {
    models.initialize_wards(wards_init);
    models.persons.reset(persons_init);
}
