"use strict";
// initialize Hoodie
var log = $("#log");
var hoodie  = new Hoodie();
var sp = sp || {};

var persons_init = [
  { name: 'Arenz', id: 'Are'},
  { name: 'Aßmann', id: 'Aßm',},
  { name: 'Enoh', id: 'Eno',},
  { name: 'Georga', id: 'Geo',},
  { name: 'Gkavagia', id: 'Gka',},
  { name: 'Kurtic', id: 'Kur',},
  { name: 'Pulawski', id: 'Pul',},
  { name: 'Rozdina', id: 'Roz',},
  { name: 'Vilvoi', id: 'Vil',},
  { name: 'Xourafa', id: 'Xou',}
];
var wards_init = [
  { name: 'Station A', id: 'A',
    min: 2, max: 3, continued: true },
  { name: 'Station B', id: 'B',
    min: 2, max: 3, continued: true },
  { name: 'Station P', id: 'P',
    min: 1, max: 2, continued: true },
  { name: 'Station IMC', id: 'IMC',
    min: 1, max: 1, continued: true },
  { name: 'Intensiv', id: 'Int',
    min: 1, max: 2, continued: true },
  { name: 'Hausdienst', id: 'D1',
    min: 0, max: 1, nightshift: true, everyday: true },
  { name: 'Intensivdienst', id: 'D2',
    min: 0, max: 1, nightshift: true, everyday: true },
  { name: 'Urlaub', id: 'Url',
    min: 0, max: 10, on_leave: true, continued: true },
];

var next_date = new Date(2015, 7, 1);
var last_day;

function add_month() {
  var content = $("#main-content");

  var month = next_date.getMonth();
  var year = next_date.getFullYear();
  var month_names = ['Januar', 'Februar', 'März', 'April', 'Mai',
    'Juni', 'Juli', 'August', 'September', 'Oktober',
    'November', 'Dezember'];

  content.append($('<h2/>', { text: month_names[month]+' '+year }));


  var table = $('<table/>', {border: 1});

  var titlerow = $('<tr/>', {'class': 'titlerow'}).append($('<th/>'));
  var d_i_m = days_in_month(month, year);
  var month_string = '.'+(month+1)+'.';
  var i;
  for (i = 0; i < d_i_m; i++) {
    titlerow.append($('<th/>', { text: (i+1) + month_string }));
  }

  table.append(titlerow);


  var days = [];
  for (i = 0; i < d_i_m; i++) {
    var new_day = new sp.Day({
      date: new Date(year, month, i+1),
      yesterday: last_day,
    });
    // new_day.store();
    days[i] = last_day = new_day;
  }
  function construct_row(model, row_name, View, collection_array) {
    var row = $('<tr/>', {'class': row_name});
    row.append($('<th/>', { text: model.get('name')}));

    for (var i = 0; i < d_i_m; i++) {
      var collection = days[i][collection_array][model.id];
      if (collection) {
        var view = new View({collection: collection});
        row.append(view.render().$el);
      } else {
        row.append('<td></td>');
      }
    }
    
  
    table.append(row);
  
  }
  sp.wards.each(function(ward) {
    construct_row(ward, 'wardrow', sp.StaffingView, 'ward_staffings');
  });
  sp.persons.each(function(person) {
    construct_row(person, 'personrow', sp.DutiesView, 'persons_duties');
  });

  content.append(table);
}

function show_addstaff(argument) {
  // body...
}
