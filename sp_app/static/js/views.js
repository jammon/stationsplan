"use strict";
var sp = sp || {};

sp.StaffingView = Backbone.View.extend({
    tagName: 'td',
    events: {
        "click": "addstaff",
    },
    initialize: function() {
        this.listenTo(this.collection, "update", this.render);
    },
    render: function() {
        var el = this.$el;
        el.empty();
        this.collection.each(function(person) {
            el.append($('<div/>', {
                text: person.id,
                'class': 'staff',
            }));
        });
        el.toggleClass('lacking', this.collection.lacking());
        return this;
    },
    addstaff: function() {
        if (!sp.can_change) return;
        sp.changestaffview.show(this.collection);
    },
});
sp.Ward.prototype.row_view = sp.StaffingView;

sp.ChangeStaffView = Backbone.View.extend({
    events: {
        "click button.changestaff": "button_clicked",
    },
    button_clicked: function(event) {
        sp.change_and_store(
            event.target.dataset.shortname,
            this.staffing,
            event.target.dataset.action);
        this.$el.modal('hide');
    },
    change_person_template: _.template(
        '<tr><td>' +
        '<button type="button" class="btn btn-primary btn-xs changestaff" ' +
        'data-shortname="<%= shortname %>" data-action="<%= action %>">' +
        '<span class="glyphicon glyphicon-<%= plus_or_minus %>"></span>' +
        '</button>' +
        '</td>' +
        '<td><%= name %></td><td><%= duties %></td></tr>'),
    add_person_html: function(person, action, dialog_body, day) {
        dialog_body.append(this.change_person_template({
            shortname: person.id,
            name: person.get('name'),
            plus_or_minus: (action=='add' ? 'plus' : 'minus'),
            action: action,
            duties: day.persons_duties[person.id].pluck('shortname').join(', '),
        }));
    },
    render: function() {
        var ward = this.staffing.ward;
        var day = this.staffing.day;
        var available = day.get_available(ward);
        var dialog_body = this.$("#changestafftable").empty();
        var that = this;
        this.$(".changedate").text(datestr(day.get('date')));
        this.$(".changeward").text(ward.get('name'));
        function datestr(date) {
            return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
        }
        this.staffing.each(function(person) {
            that.add_person_html(person, 'remove', dialog_body, day);
        });
        _.each(available, function(person) {
            that.add_person_html(person, 'add', dialog_body, day);
        });
        return this;
    },
    show: function(staffing) {
        this.staffing = staffing;
        this.render();
        this.$el.modal('show');
    },
});
sp.changestaffview = new sp.ChangeStaffView({
    el: $("#changestaff"),
});

sp.DutiesView = Backbone.View.extend({
    tagName: 'td',
    initialize: function() {
        this.listenTo(this.collection, "update", this.render);
    },
    render: function() {
        this.$el.html(this.collection.pluck('shortname').join(', '));
        return this;
    },
});
sp.Person.prototype.row_view = sp.DutiesView;

sp.AddItemView = Backbone.View.extend({
    tagName: 'tr',
    initialize: function(options) {
        this.kind = options.kind;
    },
    render: function() {
        this.$el.html('<th>+</th>');
        return this;
    },
});
