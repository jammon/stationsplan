var persons_init = [
    { name: 'Anton', id: '1', shortname: 'A', 
      functions: ['A', 'B', 'N', 'O'], departments: [1]},
    { name: 'Berta', id: '2', shortname: 'B', 
      functions: ['A', 'B', 'N', 'O'], departments: [1]},
    { name: 'Conny', id: '3', shortname: 'C', 
      functions: ['A', 'B'], departments: [1]}, // no nightshifts
    { name: 'Other', id: '4', shortname: 'Other', 
      functions: ['A', 'B'], departments: [1], anonymous: true},
    { name: 'Different Department', id: '5', shortname: 'DiffDept', 
      functions: ['A', 'B'], departments: [2]}
];
var wards_init = [
    { name: 'Ward A', id: '1', shortname: 'A', min: 1, max: 2 },
    { name: 'Ward B', id: '2', shortname: 'B', min: 2, max: 2 },
    { name: 'Nightshift', id: '3', shortname: 'N', min: 0, max: 1, after_this: 'N', 
      callshift: true, everyday: true, weight: 2, ward_type: 'Callshifts' },
    { name: 'Leave', id: '4', shortname: 'L', min: 0, max: 10, on_leave: true },
    { name: 'Free days', id: '5', shortname: 'F', min: 0, max: 10, freedays: true },
    { name: 'Visite', id: '6', shortname: 'V', min: 0, max: 10, weekdays: '6', 
      callshift: true, weight: 1 },
    { name: 'One day task', id: '7', shortname: 'O', min: 0, max: 10, 
      callshift: true, weight: 3, ward_type: 'Callshifts' },
    { name: 'Special', id: '8', shortname: 'S', min: 0, max: 10,
      after_this: 'S,A' },
];
var different_days = [
    ['V', '20150808', '-'],
    ['V', '20150809', '+'],
];
function init_hospital() {
    // models.user.is_editor = true;
    models.user.departments = {1: 'My department'};
    models.user.current_department = 1;
    models.initialize_wards(wards_init, different_days);
    models.persons.reset(persons_init);
}

