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
    change_person_template: _.template(
        '<div>' +
        '<button type="button" class="btn btn-primary btn-sm changestaff" ' +
        'data-shortname="<%= shortname %>" data-action="<%= action %>">' +
        '<%= plus_or_minus %></button> ' +
        '<%= name %></div>'),
    add_person_html: function(person, action, dialog_body) {
        dialog_body.append(this.change_person_template({
            shortname: person.id,
            name: person.get('name'),
            plus_or_minus: (action=='add' ? '+' : '-'),
            action: action,
        }));
    },
    addstaff: function() {
        if (!sp.can_change) return;
        var coll = this.collection;
        var available = coll.day.get_available(coll.ward);
        function datestr(date) {
            return date.getDate()+'.'+(date.getMonth()+1)+'.'+date.getFullYear();
        }
        $("#changestaff .changedate").text(datestr(this.collection.day.get('date')));
        $("#changestaff .changeward").text(coll.ward.get('name'));
        var dialog_body = $("#changestaff .modal-body").empty();
        var that = this;
        coll.each(function(person) {
            that.add_person_html(person, 'remove', dialog_body);
        });
        _.each(available, function(person) {
            that.add_person_html(person, 'add', dialog_body);
        });
        var dialog = $("#changestaff");
        function button_clicked (event) {
            sp.change_and_store(
                event.target.dataset.shortname, 
                that.collection,
                event.target.dataset.action);
            dialog.modal('hide');
        }
        dialog.on("click", "button.changestaff", button_clicked);
        dialog.on("hide.bs.modal", function() {
            dialog.off("click", "button.changestaff", button_clicked);
        });
        dialog.modal('show');
    },
});
sp.Ward.prototype.row_view = sp.StaffingView;

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
