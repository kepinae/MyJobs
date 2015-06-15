window.onpopstate = function(event) {
  var state = event.state,
      $sidebar = $(".sidebar"),
      historyNew,
      historyClone,
      report;

  if (state.page && state.page === 'overview') {
    navigation = false;
    renderOverview();
  } else if (state.page && state.page === 'new') {
    historyNew = function() {
      var types = state.types,
          form,
          report,
          rs;

      if (types.length > 1) {
        rs = types.map(function(type) {
          return createReport(type);
        });
        form = new Form(rs);
      } else {
        report = createReport(types[0]);
      }


      $("#container").addClass("rpt-container");
      if (form) {
        form.renderReports(".rpt-container");
      } else {
        report.renderFields(".rpt-container", report.fields, true);
        report.unbindEvent().bindEvents();
      }
      renderNavigation();
    };

    navigation = true;
    $sidebar.length > 0 ? historyNew() : renderOverview(historyNew);
  } else if (state.page && state.page === 'view-report') {
    var callback = function() {
          renderNavigation(true);
        },
        render = {
          contact: function() {return renderViewContact(state.reportId);},
          partner: function() {return renderViewPartner(state.reportId);},
          contactrecord: function() {return renderGraphs(state.reportId, callback);}
        };
    navigation = true;
    render[state.model]();
  } else if (state.page && state.page === 'report-archive') {
    navigation = true;
    renderArchive(renderNavigation);
  } else if (state.page && state.page === 'report-download') {
    renderDownload(state.report);
  } else if (state.page && state.page === 'clone') {
    historyClone = function() {
      report = createReport(state.type);
      report.createCloneReport(state.inputs);
      $("#container").addClass("rpt-container");
      report.renderFields(".rpt-container", report.fields, true);
      report.unbindEvent().bindEvents();
      renderNavigation();
    };

    navigation = true;
    $sidebar.length > 0 ? historyClone() : renderOverview(historyClone);
  }
};


// Determines if IE10+ is being used.
var modernBrowser = !(isIE() && isIE() < 10);

// Determines if a navigation bar is needed.
var navigation = false;

// Gives the ability for AJAX to send Arrays.
$.ajaxSettings.traditional = true;

function Form(reports) {
  this.reports = reports;
}

Form.prototype.renderReports = function(renderAt) {
  this.reports.forEach(function(report, index, array) {
    report.renderFields(renderAt, report.fields, index === 0, index + 1 === array.length);
  });
};


// Handles storing data, rendering fields, and submitting report. See prototype functions
function Report(type, fields) {
  this.data = {};
  this.fields = fields;
  this.type = type;

  var report = this;

  this.fields.forEach(function(field) {
    field.report = report;
  });
}

Report.prototype.renderFields = function(renderAt, fields, clear, btn) {
  var $renderAt = $(renderAt),
      c = typeof clear !== "undefined" ? clear : true,
      b = typeof btn !== "undefined" ? btn : true,
      field,
      i;

  // Clear what is currently in the container.
  if (c) {
    $renderAt.html("");
  }

  // for field in fields render.
  for (i = 0; i < fields.length; i++) {
    field = fields[i];
    if (!field.dom().length) {
      $renderAt.append(field.render());
      if (typeof field.filter !== "undefined" && !field.dependencies.length) {
        field.filter();
      }
      if (typeof field.bindEvents !== "undefined") {
        field.bindEvents();
      }
    }
  }

  if (b) {
    $renderAt.append('<div class="show-modal-holder">' +
                   '<a id="show-modal" class="btn primary">Generate Report</a>' +
                   '</div>');
  }

  return this;
};

Report.prototype.findField = function(fieldID) {
  return this.fields.filter(function(field) {
    return (field.id === fieldID ? field : undefined);
  })[0];
};

Report.prototype.createCloneReport = function(json) {
  var phony,
      value,
      date,
      key;

  for (key in json) {
    if (json.hasOwnProperty(key)) {
      value = json[key];
      if (key === "start_date" || key === "end_date") {
        phony = {};
        phony[key] = value;
        date = this.findField("date");
        $.extend(date.defaultVal, phony);
      } else {
        this.findField(key === "contact__name" ? "contact" : key).defaultVal = value;
      }
    }
  }
};

Report.prototype.bindEvents = function() {
  var report = this,
      container = $("#main-container");

  container.on("click", "#show-modal:not('.disabled')", function() {
    var modal = $("#report-modal"),
        body = modal.children(".modal-body"),
        footer = modal.children(".modal-footer"),
        saved;

    saved = report.save();

    if (saved) {
      body.html(report.readableData());
      modal.modal("show");
    }
  });

  $("body").on("click.submit", "#gen-report:not('disabled')", function() {
    var csrf = read_cookie("csrftoken"),
        data = {"csrfmiddlewaretoken": csrf},
        url = location.protocol + "//" + location.host + "/reports/view/mypartners/" + report.type,
        newList = [];
    if (report.data) {
      $.extend(data, report.data);
    }
    if (data.contact) {
      for (var i = 0; i < data.contact.length; i++) {
        var value = data.contact[i],
            name = $("#contact input[data-pk='" + value + "']").parent().text().split('(')[0].trim();
        newList.push(name);
      }
      delete data.contact;
      data.contact__name = newList;
    }

    $.ajax({
      type: 'POST',
      url: url,
      data: $.param(data, true),
      success: function (data) {
        window.location = location.protocol + '//' + location.host + location.pathname;
      }
    });
  });

  return this;
};

Report.prototype.unbindEvent = function() {
  $("body").off(".submit");
  $("#main-container").off("click");

  return this;
};

Report.prototype.hasErrors = function() {
  return this.fields.some(function(field) {
    return field.errors.length;
  });
};

Report.prototype.save = function() {
  var report = this,
      errors;

  this.fields.forEach(function(field) {
    field.validate(false);
  });

  errors = this.fields.filter(function(field) {
    return field.errors.length > 0;
  });

  if (errors.length) {
    errors.forEach(function(field) {
      field.showErrors();
    });
    return false;
  } else {
    this.fields.forEach(function(field) {
      $.extend(report.data, field.onSave());
    });
  }

  return true;
};

Report.prototype.readableData = function(d) {
  var data = d || this.data,
      html = '',
      items,
      value,
      key,
      i;

  for (key in data) {
    if (data.hasOwnProperty(key)) {
      html += "<div>";
      value = data[key];

      // Replace all '_' instances with spaces
      key = key.replace(/_/g, " ");

      if (value && value.length) {
        html += '<label>' + key.capitalize() + ':</label>';
      }

      // If value is an object (aka an array).
      if (typeof value === "object" && value !== null && value.length) {
        items = [];

        if (key === "partner" || key === "contact") {
          for (i = 0; i < value.length; i++) {
            items.push($('#' + key + ' input[data-pk='+ value[i] + ']').parent().text());
          }
        } else {
          for (i = 0; i < value.length; i++) {
            items.push(value[i]);
          }
        }
        html += '<ul class="short-list"><li>' + items.join('</li><li>') + '</li></ul>';
      } else {
        html += value;
      }
      html += '</div>';
    }
  }
  return html;
};


function Field(label, id, required, defaultVal, helpText) {
  this.label = label;
  this.id = id;
  this.required = !!required || false;
  this.defaultVal = defaultVal || '';
  this.helpText = helpText || '';
  this.errors = [];
}

Field.prototype.renderLabel = function() {
  return '<label class="big-blu" for="' + this.id + '">' + this.label + (this.required ? '<span style="color: #990000;">*</span>' : '') + '</label>';
};

Field.prototype.dom = function() {
  return $("#" + this.id);
};

Field.prototype.currentVal = function() {
  return this.dom().val();
};

// TODO: Document namespacing for binding events.
Field.prototype.bind = function(event, selector, callback) {
  if (arguments.length === 2) {
    callback = selector;
    selector = undefined;
  }

  $(this.dom()).on(event, selector, function(e) {
    callback(e);
  });

  return this;
};

// Unbinds all events of event type on this field.
Field.prototype.unbind = function(event) {
  $(this.dom()).off(event);

  return this;
};

Field.prototype.onSave = function() {
  var data = {};
  data[this.id] = this.currentVal();

  return data;
};

Field.prototype.validate = function(triggerEvent) {
  triggerEvent = typeof triggerEvent === 'undefined' ? true : triggerEvent;
  var $field = $(this.dom()),
      err = this.label + " is required",
      index = this.errors.indexOf(err);

  if (this.required && this.currentVal().trim() === "") {
    if (index === -1) {
      this.errors.push(err);
      this.showErrors();
    }
  } else {
    if (index !== -1) {
      this.errors.splice(index, 1);
      this.removeErrors();
    }

    if (triggerEvent) {
      $.event.trigger("dataChanged", [this.onSave()]);
    }
  }

  return this;
};

Field.prototype.showErrors = function() {
  var $field = $(this.dom()),
      $showModal = $("#show-modal");

  if (this.errors.length) {
    if (!$field.parent("div.required").length) {
      $field.wrap('<div class="required"></div>');
    }

    if (!$field.prev(".show-errors").length) {
      $field.before('<div class="show-errors">' + this.errors.join(', ') + '</div>');
    } else {
      $field.prev().html(this.errors.join(','));
    }
    $showModal.addClass("disabled");
  }
};

Field.prototype.removeErrors = function() {
  var $field = $(this.dom()),
      $showModal = $("#show-modal");

  if ($field.parent("div.required").length) {
    $field.prev(".show-errors").remove();
    $field.unwrap();
  }

  if (!this.report.hasErrors()) {
    $showModal.removeClass("disabled");
  }

  return this;
};


function TextField(label, id, required, defaultVal, helpText) {
  Field.call(this, label, id, required, defaultVal, helpText);
}

TextField.prototype = Object.create(Field.prototype);

TextField.prototype.render = function() {
  var label = this.renderLabel(),
      field = '<input id="' + this.id + '" value="' + this.defaultVal +
              '" type="text" placeholder="' + this.label + '" />',
      helpText = '<div class="help-text">' + this.helpText + '</div>';
  return label + field + (this.helpText ? helpText : '');
};

TextField.prototype.bindEvents = function() {
  var textField = this,
      $field = $(textField.dom()),
      trim = function() {
        var value = $field.val().trim();
        $field.val(value);
      };

  this.bind("change.validate", function(e) {
    textField.validate();
  });

  this.bind("change.trim", trim);
};


function CheckBox(label, name, defaultVal, checked, helpText) {
  this.checked = typeof checked === 'undefined' ? true : checked;
  this.name = name;
  this.id = name + '_' + defaultVal;

  Field.call(this, label, this.id, false, defaultVal, helpText);
}

CheckBox.prototype = Object.create(Field.prototype);

CheckBox.prototype.render = function(createLabel) {
  createLabel = typeof createLabel === 'undefined' ? true : createLabel;

  var label = this.renderLabel(),
      field = '<label class="field"><input id="' + this.id + '" name="' + this.name +
              '" type="checkbox" value="' + this.defaultVal + 
              (this.checked ? '" checked />' : '" />') + this.label + '</label>',
      helpText = '<div class="help-text">' + this.helpText + '</div>';

  return (createLabel ? label : '') + field + (this.helpText ? helpText : '');
};


function CheckList(label, id, choices, required, defaultVal, helpText) {
  this.choices = choices;

  Field.call(this, label, id, required, defaultVal, helpText);
}

CheckList.prototype = Object.create(Field.prototype);

CheckList.prototype.render = function() {
  var label = this.renderLabel(),
      html = $.map(this.choices, function(choice) {
        return choice.render(false);
      }).join("  ");

  return label + '<div class="checklist" id="' + this.id + '">' +
                 '<label style="display: inline;"><input value="all" type="checkbox" checked/ >All</label>  ' + html +
                 '</div>';
};

CheckList.prototype.currentVal = function() {
  var values = $.map(this.choices, function(c) {
    if (c.checked) {
      return c.currentVal();
    }
  });

  return values.length ? values : ["0"];
};

CheckList.prototype.bindEvents = function() {
  var checklist = this;

  this.bind("change", "[value='all']", function(e) {
    var $all = $(e.currentTarget),
        $choices = $(checklist.dom()).find(".field input");

    $choices.prop("checked", $all.is(":checked"));
    $($choices[$choices.length - 1]).change();
  });

  this.bind("change", ".field input", function(e) {
    var $choice = $(e.currentTarget),
        choices = $(checklist.dom()).find(".field input").toArray(),
        $all = $(checklist.dom()).find("[value='all']"),
        checked;

    checked = choices.every(function(c) { return $(c).is(":checked"); });
    $all.prop("checked", checked);

    checklist.choices.forEach(function(element) {
      element.checked = $(element.dom()).is(":checked");
    });

    checklist.validate(); 
  });
};

CheckList.prototype.validate = function(triggerEvent) {
  triggerEvent = typeof triggerEvent === 'undefined' ? true : triggerEvent;
  var err = this.label + " is required",
      index = this.errors.indexOf(err),
      value = this.currentVal();
  
  if (this.required && value.indexOf("0") === 0 && value.length === 1) {
    if (index === -1) {
      this.errors.push(err);
      this.showErrors();
    }
  } else {
    if (index !== -1) {
      this.errors.splice(index, 1);
      this.removeErrors();
    }
  }

  if (triggerEvent) {
    $.event.trigger("dataChanged", [this.onSave()]);
  }

  return this;
};


function DateField(label, id, required, defaultVal, helpText) {
  var dVal = defaultVal || {};
  Field.call(this, label, id, required, dVal, helpText);
}

DateField.prototype = Object.create(Field.prototype);

DateField.prototype.render = function() {
  var label = this.renderLabel(),
      dateWidget = $('<div id="' + this.id + '" class="filter-option"><div class="date-picker"></div></div>'),
      datePicker = $(dateWidget).find(".date-picker"),
      to = '<span id="activity-to-" class="datepicker">to</span>',
      start = '<input id="start-date" class="datepicker picker-left" type="text" value="' + (this.defaultVal ? this.defaultVal.start_date : "") + '" placeholder="Start Date" />',
      end = '<input id="end-date" class="datepicker picker-right" type="text" value="' + (this.defaultVal ? this.defaultVal.end_date : "")  + '" placeholder="End Date" />';

  datePicker.append(start).append(to).append(end);
  dateWidget.append(datePicker);
  return label + dateWidget.prop("outerHTML");
};

DateField.prototype.currentVal = function(id) {
  return $(this.dom()).find("#" + id).val();
};

DateField.prototype.validate = function(triggerEvent) {
  triggerEvent = typeof triggerEvent === 'undefined' ? true : triggerEvent;
  var dateField = this,
      $dom = $(this.dom()),
      $fields = $dom.find("input.datepicker"), // Both start and end inputs.
      label,
      err;

  $.each($fields, function(index, field) {
    label = $(field).attr('placeholder');
    err = label + " is required";
    index = dateField.errors.indexOf(err);
    if ($(field).val() === "") {
      if (index === -1) {
        dateField.errors.push(label + " is required");
        dateField.showErrors();
      }
    } else {
      if (index !== -1) {
        dateField.errors.splice(index, 1);
        dateField.removeErrors();
      }
    }
  });

  if (!dateField.errors.length && triggerEvent) {
    $.event.trigger("dataChanged", [dateField.onSave()]);
  }

  return this;
};

DateField.prototype.bindEvents = function() {
  var dateField = this,
      datePicker = function(e) {
        var $targeted = $(e.currentTarget);
        $targeted.pickadate({
          format: "mm/dd/yyyy",
          selectYears: true,
          selectMonths: true,
          min: [2014, 0, 1], // PRM started in 2014/1/1
          max: true,
          today: false,
          clear: false,
          close: false,
          onOpen: function() {
            if(this.get("id") === "start-date") {
              var end_date = $("#end-date").val();
              this.set("max", end_date ? new Date(end_date) : true);
            } else if (this.get("id") === "end-date") {
              var start_date = $("#start-date").val();
              this.set("min", start_date ? new Date(start_date) : [2014, 0, 1]);
            }
          }
        });
    };

  this.bind("focus.datepicker", ".datepicker", datePicker);
  this.bind("change.validate", ".datepicker", function(e) {
    dateField.validate();
  });
};

DateField.prototype.onSave = function() {
  var data = {};
  data.start_date = this.currentVal("start-date");
  data.end_date = this.currentVal("end-date");
  return data;
};


function StateField(label, id, required, defaultVal, helpText) {
  Field.call(this, label, id, required, defaultVal, helpText);
}

StateField.prototype = Object.create(Field.prototype);

StateField.prototype.render = function() {
  var label = this.renderLabel(),
      $select = $('<select id="' + this.id + '"></select>'),
      options = ['<option value="">Select a State</option>'],
      st;

  // create options
  for (st in states) {
    if (states.hasOwnProperty(st)) {
      options.push('<option value="' + st + '" ' + (this.defaultVal === st ? "selected" : "") + '>' + states[st] + '</option>');
    }
  }

  $select.append(options.join(''));
  return label + $select.prop("outerHTML");
};

StateField.prototype.bindEvents = function() {
  var stateField = this;

  $(document).on("change.validate", "#" + stateField.id, function() {
    stateField.validate();  
  });
};


function TagField(label, id, required, defaultVal, helpText) {
  this.value = [];
  TextField.call(this, label, id, required, defaultVal, helpText);
}

TagField.prototype = Object.create(TextField.prototype);

TagField.prototype.bindEvents = function() {
  var tagField = this,
      $dom = $(this.dom());

  $dom.autocomplete({
    focus: function() {
      // Prevent value inserted on focus.
      return false;
    },
    select: function(event, ui) {
      // Split string by "," then trim whitespace on either side of all inputs.
      var inputs = this.value.split(",").map(function(i) {return i.trim();});

      // Remove last element of inputs. Typically is an unfinished string.
      inputs.pop();
      // Add selected item from autocomplete
      inputs.push(ui.item.value);
      // Add placeholder for join to create an extra ", " for UX goodness.
      inputs.push("");
      // Combine everything in inputs with ", ".
      this.value = inputs.join(", ");

      // If there are any inputs already in the field make sure default functionality doesn't run.
      if (inputs.length) {
        return false;
      }
    },
    source: function(request, response) {
      var inputs = request.term.split(",").map(function(i) {return i.trim();}),
          // Last element is always going to be what is being searched for.
          keyword = inputs.pop(),
          // Initialize list of suggested tag names.
          suggestions;

      $.ajax({
        type: "GET",
        url: "/reports/ajax/mypartners/tag",
        //TODO: New backend changes will fix this monstrocity
        data: {name: keyword,
               contact__isnull: true,
               partner__isnull: true,
               partnersavedsearch__isnull: true,
               contactrecord__isnull: false,
               values: ["name"],
               order_by: "name"},
        success: function(data) {
          suggestions = data.filter(function(d) {
            // Don't suggest things that are already selected.
            if (inputs.indexOf(d.name) === -1) {
              return d;
            }
          }).map(function(d) {
            // Only care about name string.
            return d.name;
          });

          response(suggestions);
        }
      });
    }
  });

  $dom.on("autocompleteopen", function() {
    $dom.data("isOpen", true);
  });

  $dom.on("autocompleteclose", function() {
    $dom.data("isOpen", false);
    tagField.value = $dom.val();
    tagField.validate();
  });

  $dom.on("change", function() {
    if(!$dom.data("isOpen")) {
      tagField.value = $dom.val();
      tagField.validate();
    }
  });
};

TagField.prototype.currentVal = function() {
  // Split on commas. Trim each element in array. Remove any elements that were blank strings.
  // #2proud2linebreak
  return this.dom().val().split(",").map(function(t) { return t.trim(); }).filter(function(t) { if (!!t) { return t; } });
};


function FilteredList(label, id, required, ignore, dependencies, defaultVal, helpText) {
  this.ignore = ignore || [];
  this.dependencies = dependencies || [];
  this.active = 0;
  this.hasRan = false;

  Field.call(this, label, id, required, defaultVal, helpText);
}

FilteredList.prototype = Object.create(Field.prototype);

FilteredList.prototype.renderLabel = function() {
  return '<div id="'+ this.id +'-header" class="list-header">' +
         '<i class="fa fa-plus-square-o"></i>' +
         '<input id="' + this.id + '-all-checkbox" type="checkbox" ' + (this.defaultVal ? "" : "checked") + ' />' +
         ' All ' + this.label + (this.required ? '<star style="color: #990000">*</star>' : '') +
         ' <span>(<span class="record-count">0</span> ' + this.label + ' Selected)</span>' +
         '</div>';
};

FilteredList.prototype.render = function() {
  var label = this.renderLabel(),
      body = '<div id="' + this.id + '" style="display: none;" class="list-body"></div>';

  return label + body;
};

FilteredList.prototype.filter = function() {
  var filteredList = this,
      filterData = {},
      $recordCount,
      $listBody,
      $input,
      Status = { UNPROCESSED: 0, APPROVED: 1, DENIED: 2 };

  filteredList.report.fields.forEach(function(field) {
    if (filteredList.ignore.indexOf(field.id) === -1) {
      $.extend(filterData, field.onSave());
    }
  });

  // only show approved records
  filterData.approval_status__code=Status.APPROVED;

  if (this.id === "partner") {
    // annotate how many records a partner has.
    $.extend(filterData, {
      values: ["pk", "name"],
      order_by: "name"
    });

  } else if (this.id === "contact") {
    $.extend(filterData, {values: ["pk", "name", "email"], order_by: "name"});
  }

  filterData.contactrecord__tags__name = filterData.tags__name;
  delete filterData.tags__name;

  $.ajax({
    type: "GET",
    url: "/reports/ajax/mypartners/" + this.id,
    data: filterData,
    global: false,
    beforeSend: function() {
      $('#' + filteredList.id + '-header > span').hide();
      if (!$('#' + filteredList.id + '-header > .fa-spinner').length) {
        $('#' + filteredList.id + '-header').append('<i style="margin-left: 5px;" class="fa fa-spinner fa-pulse"></i>');
      }
      filteredList.active++;
    },
    success: function(data) {
      $recordCount = $('#' + filteredList.id + '-header .record-count');
      $listBody = $('.list-body#' + filteredList.id);
      $listBody.html("").parent(".required").children().unwrap().prev('.show-errors').remove();
      $listBody.append('<ul><li>' + data.map(function(element) {
        $input = $('<input type="checkbox" data-pk="' + element.pk + '" ' + (function () {
          if (filteredList.defaultVal && !filteredList.hasRan) {
            if (filteredList.id === "contact") {
              return filteredList.defaultVal.indexOf(element.name) >= 0 ? "checked" : "";
            } else {
              return filteredList.defaultVal.indexOf(element.pk.toString()) >= 0 ? "checked" : "";
            }
          }
          return "checked";
        })() +  '/>');
        return '<label>' + $input.prop("outerHTML") + ' ' + element.name +
          (filteredList.id === 'contact' && element.email ? ' <span class="small">(' + element.email + ')</span>' : '') + '</label>';
      }).join("</li><li>") + '</li></ul>');

      var value = filteredList.currentVal();
      if (!filteredList.hasRan) {
        $('#' + filteredList.id + '-header input').prop("checked", $(filteredList.dom()).find("input").toArray().every(function(c) { return $(c).is(":checked"); }));
      } else {
        $('#' + filteredList.id + '-header input').prop("checked", true);
      }
      $recordCount.text(value.length === 1 && value.indexOf("0") === 0 ? 0 : value.length);

      $.event.trigger("filtered", [filteredList]);
    }
  }).done(function() {
    filteredList.active--;
    if (!filteredList.active) {
      $('#' + filteredList.id + '-header > .fa-spinner').remove();
      $('#' + filteredList.id + '-header > span').show();
    }
    filteredList.validate(false);
    filteredList.hasRan = true;
  });
};

FilteredList.prototype.currentVal = function() {
  var values = $.map($(this.dom()).find("input").toArray(), function(c) {
    if (c.checked) {
      return $(c).data("pk");
    }
  });

  return values.length ? values : ["0"];
};

FilteredList.prototype.bindEvents = function() {
  var filteredList = this,
      $header = $('#' + filteredList.id + '-header'),
      $recordCount = $header.find(".record-count"),
      $all = $header.find("input"),
      $dom = $(this.dom());

  $header.on("click", function() {
    var $this = $(this),
        $icon = $this.children("i:first");

    if ($icon.hasClass("fa-plus-square-o")) {
      $icon.removeClass("fa-plus-square-o").addClass("fa-minus-square-o");
    } else {
      $icon.removeClass("fa-minus-square-o").addClass("fa-plus-square-o");
    }

    $this.next().stop(true, true).slideToggle();
  });

  $header.on("change", "input", function() {
    var $choices = $(filteredList.dom()).find("input");

    $choices.prop("checked", $(this).is(":checked"));
    $($choices[$choices.length - 1]).change();
  });

  $header.on("click", "input", function(e) {
    e.stopPropagation();
  });

  $dom.bind("change", "input", function() {
    var choices = $(filteredList.dom()).find("input").toArray(),
        checked;

    checked = choices.every(function(c) { return $(c).is(":checked"); });
    $all.prop("checked", checked);
    var value = filteredList.currentVal();
    $recordCount.text(value.length === 1 && value.indexOf("0") === 0 ? 0 : value.length);
    $.event.trigger("filtered", [filteredList]);
  });

  $all.on("change", function(e) {
    filteredList.validate();
  });

  $dom.bind("change.validate", "input", function(e) {
    filteredList.validate();
  });

  // TODO: Figure out how to reduce queries; perhaps by diffing total changes
  $dom.on("dataChanged", function(e, data) {
    var callFilter = !filteredList.dependencies.length && filteredList.ignore.every(function(element) {
          return !(element in data);
        });

    if(callFilter) {
      filteredList.filter();
    }

  });

  $dom.on("filtered", function(e, field) {
    if (filteredList.dependencies.indexOf(field.id) !== -1) {
      filteredList.filter();
    }
  });
};

FilteredList.prototype.validate = function(triggerEvent) {
  triggerEvent = typeof triggerEvent === 'undefined' ? true : triggerEvent;
  var err = this.label + " is required",
      index = this.errors.indexOf(err),
      value = this.currentVal();

  if (this.required && value.indexOf("0") === 0 && value.length === 1) {
    if (index === -1) {
      this.errors.push(err);
      this.showErrors();
    }
  } else {
    if (index !== -1) {
      this.errors.splice(index, 1);
      this.removeErrors();
    }
  }

  if (triggerEvent) {
    $.event.trigger("dataChanged", [this.onSave()]);
  }

  return this;
};

FilteredList.prototype.showErrors = function() {
  var $header = $('#' + this.id + '-header'),
      $fuse = $('#' + this.id + '-header, #' + this.id),
      $showModal = $('#show-modal');

  if (this.errors.length) {
    if (!$fuse.parent(".required").length) {
      $fuse.wrapAll('<div class="required"></div>');
    }

    if (!$header.prev(".show-errors").length) {
      $header.before('<div class="show-errors">' + this.errors.join(', ') + '</div>');
    } else {
      $header.prev().html(this.errors.join(','));
    }
    $showModal.addClass("disabled");
  }

  return this;
};

FilteredList.prototype.removeErrors = function() {
  var $header = $('#' + this.id + '-header'),
      $showModal = $('#show-modal');

  if ($header.parent(".required").length) {
    $header.prev(".show-errors").remove();
    $header.unwrap();
  }

  if (!this.report.hasErrors()) {
    $showModal.removeClass("disabled");
  }

  return this;
};


// Capitalize first letter of a string.
String.prototype.capitalize = function() {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

var yesterday = (function(d){d.setDate(d.getDate() - 1); return d; })(new Date());


$(document).ready(function() {
  var subpage = $(".subpage");

  $("#choices input[name='report']:checked").prop("checked", false);

  if (modernBrowser) {
    history.replaceState({'page': 'overview'}, "Report Overview");
  }

  subpage.on("click", "#start-report:not(.disabled)", function(e) {
    e.preventDefault();
    var choices = $("#choices input[name='report']:checked"),
        types = [],
        i = 0,
        form,
        rs,
        report;

    // fill types with choices that are checked, see selector.
    for (i; i < choices.length; i++) {
      types.push(choices[i].value.toLowerCase());
    }

    if (types.length > 1) {
      rs = types.map(function(type) {
        return createReport(type);
      });
      form = new Form(rs);
    } else {
      report = createReport(types[0]);
    }

    // Create js Report object and set up next step.
    if (modernBrowser) {
      history.pushState({'page': 'new', 'report': report, types: types}, 'Create Report');
    }

    $("#container").addClass("rpt-container");
    if (form) {
      form.renderReports(".rpt-container");
    } else {
      report.renderFields(".rpt-container", report.fields, true);
      report.unbindEvent().bindEvents();
    }
  });

  subpage.on("click", "#choices input[name='report']", function() {
    var $checkboxes = $("#choices input[name='report']"),
        $startReport = $("#start-report");

    if ($checkboxes.is(":checked")) {
      $startReport.removeClass("disabled");
    } else {
      $startReport.addClass("disabled");
    }
  });

  // View Report
  subpage.on("click", ".report > a, .fa-eye:not(.disabled), .view-report:not(.disabled)", function() {
    var report_id = $(this).parents("tr, .report").data("report"),
        model = $(this).parents("tr, .report").data("model"),
        callback = function() {
          renderNavigation(true);
        },
        views = {
          partner: function() {return renderViewPartner(report_id);},
          contact: function() {return renderViewContact(report_id);},
          contactrecord: function() {return renderGraphs(report_id, callback);}
        };

    if (modernBrowser) {
      history.pushState({page: 'view-report', model: model, reportId: report_id}, 'View Report');
    }

    views[model]();
  });

  // Clone Report
  subpage.on("click", ".fa-copy, .clone-report", function() {
    var data = {id: $(this).parents("tr, .report").data("report"),
                values: ['name', 'model', 'app', 'params']},
        url = location.protocol + "//" + location.host, // https://secure.my.jobs
        cloneReport = function() {
          $.ajax({
            type: "GET",
            url: url + "/reports/ajax/myreports/report",
            data: data,
            dataType: "json",
            success: function(data) {
              var reportData = data[0],
                  model = reportData.model,
                  params = JSON.parse(reportData.params),
                  report = createReport(model);

              $.extend(params, {report_name: "Copy of " + reportData.name.replace(/_/g, " ")});

              report.createCloneReport(params);

              $("#container").addClass("rpt-container");
              report.renderFields(".rpt-container", report.fields, true);
              report.unbindEvent().bindEvents();

              if (modernBrowser) {
                history.pushState({'page': 'clone', 'inputs': params, 'type': report.type}, "Clone Report");
              }
            }
          });
        };

    if ($(this).attr("id") !== undefined) {
      cloneReport();
    } else {
      renderOverview(cloneReport);
    }

    navigation = true;
    renderNavigation();
  });

  subpage.on("click", ".fa-download:not(.disabled), .export-report:not(.disabled)", function() {
    var report_id = $(this).parents("tr, .report").data("report");

    if (modernBrowser) {
      history.pushState({'page': 'report-download', 'report': report_id}, 'Download Report');
    }

    renderDownload(report_id);
  });

  subpage.on("click", ".fa-refresh:not('.fa-spin'), .regenerate-report", function() {
    var report_id,
        data,
        $icon = $(this),
        $div,
        archive = false,
        url = location.protocol + "//" + location.host; // https://secure.my.jobs

    if (typeof $(this).attr("id") !== "undefined") {
      report_id = $(this).attr("id").split("-")[1];
    } else {
      $icon = $(this).children(".fa-refresh");
      $div = $(this);
      report_id = $(this).parents("tr").data("report");
      archive = true;

      if ($(this).children(".fa-spin").length) {
        return false;
      }
    }

    data = {'id': report_id};

    $.ajax({
      type: "GET",
      url: url + "/reports/ajax/regenerate",
      global: false,
      data: data,
      beforeSend: function() {
        $icon.addClass("fa-spin");
      },
      success: function() {
        $icon.removeClass("fa-spin");

        if (archive) {
          $div.parents('tr').find('.export-report, .view-report').removeClass('disabled');
        } else {
          $icon.parents('div.report').find('.report-link, .fa-eye, .fa-download').removeClass('disabled');
        }
      }
    });
  });

  // View Archive
  subpage.on("click", "#report-archive", function() {
    if (modernBrowser) {
      history.pushState({'page': 'report-archive'}, "Report Archive");
    }
    navigation = true;
    renderArchive(renderNavigation);
  });
});


// Checks to see if browser is IE. If it is then get version.
function isIE() {
    var myNav = navigator.userAgent.toLowerCase();
    return (myNav.indexOf('msie') !== -1) ? parseInt(myNav.split('msie')[1]) : false;
}


function createReport(type) {
  var reports = {
  contact: function() {
    return new Report("contact", [new TextField("Report Name", "report_name", true, reportNameDateFormat(new Date())),
                                  new DateField("Select Date", "date", true, {start_date: "01/01/2014", end_date: dateFieldFormat(yesterday)}),
                                  new StateField("State", "state", false),
                                  new TextField("City", "city", false),
                                  new FilteredList("Partners", "partner", true, ["report_name", "partner"])]);
  },
  partner: function() {
    return new Report("partner", [new TextField("Report Name", "report_name", true, reportNameDateFormat(new Date())),
                                  new StateField("State", "state", false),
                                  new TextField("City", "city", false),
                                  new TextField("URL", "uri", false),
                                  new TextField("Source", "data_source", false)]);
  },
  contactrecord: function() {
    var contactTypeChoices = [new CheckBox("Email", "contact_type", "email"),
                              new CheckBox("Phone Call", "contact_type", "phone"),
                              new CheckBox("Meeting or Event", "contact_type", "meetingorevent"),
                              new CheckBox("Job Followup", "contact_type", "job"),
                              new CheckBox("Saved Search Email", "contact_type", "pssemail")];

    return new Report("contactrecord", [new TextField("Report Name", "report_name", true, reportNameDateFormat(new Date())),
                                        new DateField("Select Date", "date", true, {start_date: "01/01/2014", end_date: dateFieldFormat(yesterday)}),
                                        new StateField("State", "state", false),
                                        new TextField("City", "city", false),
                                        new CheckList("Contact Types", "contact_type", contactTypeChoices, true, "all"),
                                        new TagField("Tags", "tags__name", false, undefined, "Use commas for multiple tags."),
                                        new FilteredList("Partners", "partner", true, ["report_name", "partner", "contact"]),
                                        new FilteredList("Contacts", "contact", true, ["report_name", "contact"], ["partner"])]);
  }
};

  return reports[type]();
}


function reportNameDateFormat(date) {
  var year = date.getFullYear(),
      month = date.getMonth(),
      day = date.getDate(),
      hours = date.getHours(),
      minutes = date.getMinutes(),
      seconds = date.getSeconds(),
      milliseconds = date.getMilliseconds();

  month = turnTwoDigit(parseInt(month) + 1);
  day = turnTwoDigit(day);
  hours = turnTwoDigit(hours);
  minutes = turnTwoDigit(minutes);
  seconds = turnTwoDigit(seconds);

  return year + "-" + month + "-" + day + " " + hours + ":" + minutes + ":" + seconds + "." + milliseconds;
}


function dateFieldFormat(date) {
  var day = date.getDate(),
      month = date.getMonth(),
      year = date.getFullYear();

  day = turnTwoDigit(day);
  month = turnTwoDigit(parseInt(month) + 1);

  return month + "/" + day + "/" + year;
}


function turnTwoDigit(value) {
  return value < 10 ? "0" + value : value;
}


function pieOptions(height, width, chartArea_top, chartArea_left, chartArea_height, chartArea_width,
                    piehole_radius, slice_colors, show_tooltips) {
  var options = {legend: 'none', pieHole: piehole_radius, pieSliceText: 'none',
                 height: height, width: width,
                 chartArea: {top:chartArea_top, left:chartArea_left,
                             height: chartArea_height, width: chartArea_width},
                 slices: slice_colors
                };
  if(!show_tooltips) {
    options.tooltip = { trigger: 'none' };
  }
  return options;
}

var $navigationBar = $("#navigation");

function renderNavigation(download) {
  var mainContainer = $('#main-container'),
      $navigationBar = $navigationBar || $("#navigation");

  if (navigation) {
    if (!$navigationBar.length) {
      $navigationBar = $('<div id="navigation" class="span12" style="display:none;"></div>').append(function() {
        var $row = $('<div class="row"></div>'),
            $column1 = $('<div class="span4"></div>'),
            $column2 = $column1.clone(),
            $column3 = $column1.clone(),
            $span = $('<span id="goBack"> Back</span>'),
            $i = $('<i class="fa fa-arrow-circle-o-left fa-2x"></i>'),
            $download;

        $span.prepend($i);
        $span.on("click", function() {
          if (modernBrowser) {
            history.back();
          } else {
            renderOverview();
          }
        });
        $row.append($column1.append($span));

        if (download) {
          $download = $('<i class="fa fa-download"></i>');
          $column3.append($download);
        }

        $row.append($column2).append($column3);

        return $row;
      });
      mainContainer.prepend($navigationBar);
    }
    // TODO: Uncomment once UI for navbar is done.
    //$navigationBar.show();
  } else {
    $navigationBar.remove();
  }
}


function renderOverview(callback) {
  $.ajax({
    type: 'GET',
    url: window.location,
    data: {},
    global: false,
    success: function(data) {
      $(".subpage > .wrapper").html(data);
    }
  }).complete(function() {
    if (typeof callback === "function") {
      callback();
    }
  });
}

function renderDownload(report_id) {
  var data = {'id': report_id};

  $.ajax({
    type: "GET",
    url: "downloads",
    data: data,
    success: function(data) {
      var ctx,
          values,
          $order,
          $column,
          $columnNames,
          $allCheckbox,
          $checkboxes,
          $checked;

      function updateValues() {
        $checked = $(".column-container .enable-column:checked");
        $order = $(".sort-order");
        $column = $("#column-choices");
        $columnNames = $("#column-choices option:not([value=''])");

        values = $.map($checked, function(item) {
          return $(item).val();
        });

        $columnNames.each(function() {
          $(this).prop("disabled", values.indexOf($(this).val()) === -1);
        });

        ctx = {'id': report_id, 'values': values};
        if ($column.val()) {
          ctx.order_by = $order.val() + $column.val();
        }

        $("#download-csv").attr("href", "download?" + $.param(ctx));
      }

      $("#main-container").html(data);

      $allCheckbox = $(".enable-all-columns .enable-column");
      $checkboxes = $(".column-container .enable-column");
      $checked = $(".column-container .enable-column:checked");

      $allCheckbox.prop("checked", $checkboxes.length === $checked.length);
      updateValues();

      // Event Handlers
      $(".column-container").sortable({
        axis: "y",
        placeholder: "placeholder",
        containment: "parent",
        tolerance: "pointer",
        distance: 10,
        start: function(e, ui) {
          ui.item.addClass("drag");
        },
        stop: function(e, ui) {
          ui.item.removeClass("drag");
        },
        update: updateValues
      });

      $(".enable-all-columns .enable-column").on("change", function() {
        $("input.enable-column").prop("checked", $(this).is(":checked"));
      });

      $("input.enable-column").on("change", function() {
        $checkboxes = $(".column-wrapper .enable-column");
        $checked = $(".column-wrapper .enable-column:checked");
        $allCheckbox = $(".enable-all-columns .enable-column");

        $allCheckbox.prop("checked", $checkboxes.length === $checked.length);
      });

      $("#download-cancel").on("click", function() {
        if (modernBrowser) {
          history.back();
        } else {
          renderOverview();
        }
      });

      $("#column-choices").on("change", updateValues);
      $(".sort-order").on("change", updateValues);

      $(".enable-column").on("change", function() {
        updateValues();
      });
    }
  });
}


function renderGraphs(report_id, callback) {
  var data = {'id': report_id},
      url = location.protocol + "//" + location.host; // https://secure.my.jobs

  navigation = true;

  $.ajax({
    type: "GET",
    url: url + "/reports/view/mypartners/contactrecord",
    data: data,
    success: function(data) {
      var contacts = data.contacts,
          communications = data.communications || 0,
          emails = data.emails || 0,
          pss = data.searches || 0,
          calls = data.calls || 0,
          meetings = data.meetings || 0,
          referrals = data.referrals || 0,
          applications = data.applications || 0,
          interviews = data.interviews || 0,
          hires = data.hires || 0,
          pChartInfo = {0: {'name': "Emails",            'count': emails,   'color': "#5EB95E"},
                        1: {'name': "PSS Emails",        'count': pss,      'color': "#4BB1CF"},
                        2: {'name': "Phone Calls",       'count': calls,    'color': "#FAA732"},
                        3: {'name': "Meetings & Events", 'count': meetings, 'color': "#5F6C82"}},
          bChartInfo = {0: {'name': "Applications", 'count': applications, 'style': "color: #5EB95E"},
                        1: {'name': "Interviews",   'count': interviews,   'style': "color: #4BB1CF"},
                        2: {'name': "Hires",        'count': hires,        'style': "color: #FAA732"},
                        3: {'name': "Records",      'count': referrals,    'style': "color: #5F6C82"}};

      // Grab google's jsapi to load chart files.
      $.getScript("https://www.google.com/jsapi", function() {
        // Had to use 'callback' with google.load otherwise after load google makes a new document
        // with just <html> tags.
        google.load("visualization", "1.0", {'packages':["corechart"], 'callback': function() {
          var pDataTable = [['Records', 'All Records']], // p for pieChart
              bDataTable = [['Activity', 'Amount', {'role': 'style'}]], // b for barChart
              $mainContainer = $("#main-container"),// the container everything goes in
              pSliceOptions = {}, // slice options for pieChart
              pLegend = [], // array that will hold the report-boxes for pieChart
              bLegend = [], // array that will hold the report-boxes for barChart
              pChartData,
              pKey,
              pValue,
              pBox,
              pOptions,
              pChart,
              $pLegend,
              $pChart,
              bChartData,
              bValue,
              bKey,
              bBox,
              bOptions,
              bChart,
              $bLegend,
              topThreeRow,
              restRow,
              contactContainer,
              i;

          $mainContainer.html('').append("<div class='span6'><h4>Communication Activity</h4><div id='d-chart'></div>" +
                                         "</div><div class='span6'><h4>Referral Activity</h4><div id='b-chart'></div></div>");

          for (pKey in pChartInfo) {
            if (pChartInfo.hasOwnProperty(pKey)) {
              pValue = pChartInfo[pKey];
              pDataTable.push([pValue.name, pValue.count]);

              // Used for PieChart to give data 'slices' color.
              pSliceOptions[pKey] = {'color': pValue.color};

              // Create legend boxes
              pBox = $('<div class="report-box" style="background-color: ' +
                       pValue.color + '"><div class="big-num">' + pValue.count +
                       '</div><div class="reports-record-type">' + pValue.name + '</div></div>');
              pLegend.push(pBox);
            }
          }

          pChartData = google.visualization.arrayToDataTable(pDataTable);
          pOptions = pieOptions(330, 350, 12, 12, 300, 330, 0.6, pSliceOptions, true);
          pChart = new google.visualization.PieChart(document.getElementById('d-chart'));
          pChart.draw(pChartData, pOptions);

          $pChart = $("#d-chart > div");
          $pChart.append("<div class='chart-box-holder legend'></div>");
          $pLegend = $("#d-chart .legend");
          pLegend.forEach(function(element) {
            $pLegend.append(element);
          });

          $pChart.append('<div class="piehole report"><div class="piehole-big">' + communications +
                         '</div><div class="piehole-topic">Contact Records</div></div>');

          for (bKey in bChartInfo) {
            if (bChartInfo.hasOwnProperty(bKey)) {
              bValue = bChartInfo[bKey];
              bDataTable.push([bValue.name, bValue.count, bValue.style]);

              bBox = $('<div class="report-box" style="background-' + bValue.style +
                       '"><div class="big-num">' + bValue.count +
                       '</div><div class="reports-record-type">' + bValue.name + '</div></div>');
              bLegend.push(bBox);
            }
          }

          bChartData = google.visualization.arrayToDataTable(bDataTable);
          bOptions = {title: 'Referral Records', width: 356, height: 360, legend: { position: "none" },
                      chartArea: {top: 22, left: 37, height: 270, width: 290},
                      animation: {startup: true, duration: 400}};
          bChart = new google.visualization.ColumnChart(document.getElementById('b-chart'));
          bChart.draw(bChartData, bOptions);

          $bLegend = $('<div class="chart-box-holder legend"></div>').append(function() {
            return bLegend.map(function(element) {
              return element.prop("outerHTML");
            }).join('');
          });

          $("#b-chart > div").append($bLegend);

          // Show the top three contacts in a different format than the rest.
          topThreeRow = $('<div class="row"></div>').append(function() {
            var html = '',
                cLength = contacts.length,
                contact,
                name,
                email,
                cReferrals,
                commRecords,
                div,
                topLength;

            // Determine how long topLength should be.
            topLength = (cLength > 3) ? 3 : cLength;

            // Just run for the first 3 contacts.
            for (i = 0; i < topLength; i++) {
              // remove first contact in array, returns the removed contact.
              contact = contacts[i];
              name = contact.contact__name;
              email = contact.contact_email;
              cReferrals = contact.referrals;
              commRecords = contact.records;

              // create container
              div = $('<div class="span4 panel top-contacts"></div>');
              div.append('<div class="name">' + name + '</div><div>' + email + '</div><div class="top-three-box-container">' +
                         '<div class="report-box small"><div class="big-num">' + commRecords +
                         '</div><div class="reports-record-type">Contact Records</div></div>' +
                         '<div class="report-box small"><div class="big-num">' + cReferrals +
                         '</div><div class="reports-record-type">Referral Records</div></div></div>');

              // add the rendered html as a string.
              html += div.prop("outerHTML");
            }
            return html;
          });

          // Don't generate a table if cLength = 0
          if (contacts.length) {
            restRow = $('<div class="row"></div>').append(function() {
              var div = $('<div class="span12"></div>'),
                  table = $('<table class="table table-striped report-table"><thead><tr><th>Name</th>' +
                            '<th>Email</th><th>Partner</th><th>Contact Records</th><th>Referral Reocrds</th>' +
                            '</tr></thead></table>'),
                  tbody = $('<tbody></tbody>');
              tbody.append(function() {
                // turn each element into cells of a table then join each group of cells with rows.
                return "<tr class='report'>" + contacts.map(function(contact) {
                  return "<td data-name='" + contact.contact__name + "' data-email='" + contact.contact_email + "' data-partner='" + contact.partner + "'>" + contact.contact__name + "</td><td>" + contact.contact_email +
                         "</td><td>" + contact.partner__name + "</td><td>" + contact.records + "</td><td>" + contact.referrals + "</td>";
                }).join('</tr><tr class="report">') + "</tr>";
              });
              tbody.find("tr").on("click", function(e) {
                var row = e.currentTarget,
                    $td = $(row).find("td:first"),
                    name = $td.data("name"),
                    email = $td.data("email"),
                    partner = $td.data("partner");
                
                window.open("/prm/view/records?partner=" + partner + "&contact=" + name + "&keywords=" + email, "_blank");
              });

              return div.append(table.append(tbody));

            });
          } else {
            // Make sure topThreeRow didn't run before saying there are no records.
            if (topThreeRow.find("div.top-contacts").length === 0) {
              restRow = $('<div class="row"><div class="span12">This report has no contacts with records.</div></div>');
            }
          }

          contactContainer = $('<div id="report-contacts" class="span12"></div>').append(topThreeRow).append(restRow);
          $("#main-container").append(contactContainer);

          if (typeof callback === "function") {
            callback();
          }
        }});
      });
    }
  });
}


function renderViewPartner(id) {
  var data = {id: id},
      url = location.protocol + "//" + location.host; // https://secure.my.jobs

  $.ajax({
    type: "GET",
    url: url + "/reports/view/mypartners/partner",
    data: data,
    success: function(data) {
      var $span = $('<div class="span12"></div>'),
          $table = $('<table class="table table-striped report-table"><thead><tr>' +
                     '<th>Name</th><th>Primary Contact</th></tr></thead></table>'),
          $tbody = $('<tbody></tbody>'),
          $mainContainer = $("#main-container");

      $tbody.append(function() {
        return '<tr class="record">' + data.map(function(record) {
            return '<td>' + record.name + '</td><td>' + record.primary_contact + '</td>';
          }).join('</tr><tr>') + '</tr>';
      });

      $mainContainer.html("").append($span.append($table.append($tbody)));
    }
  });
}


function renderViewContact(id) {
   var data = {id: id},
      url = location.protocol + "//" + location.host; // https://secure.my.jobs

  $.ajax({
    type: "GET",
    url: url + "/reports/view/mypartners/contact",
    data: data,
    success: function(data) {
      var $span = $('<div class="span12"></div>'),
          $table = $('<table class="table table-striped report-table"><thead><tr>' +
                     '<th>Partner</th><th>Name</th><th>Phone</th><th>Email</th><th>State(s)</th></tr></thead></table>'),
          $tbody = $('<tbody></tbody>'),
          $mainContainer = $("#main-container"),
          location;

      // Append content to Table's tbody.
      $tbody.append('<tr class="record">' + data.map(function(record) {
        // Create a list of States based off of locations
        // in a format of City, State
        location = record.locations.map(function(location) {
            // for each location get state and trim whitespace
            return (location.split(',')[1] || '').trim();
            // Determine uniqueness
          }).sort().filter(function(e, i, a) {
            // Due to sort, duplicates will be together.
            // Check to see if this element is not the same as the prior one.
            return e !== a[i - 1];
          }).join(', ');

        return '<td>' + record.partner + '</td><td>' + record.name + '</td><td>' + record.phone + '</td>' +
               '<td>' + record.email + '</td><td>' + location + '</td>';
        }).join('</tr><tr>') + '</tr>'
      );

      $mainContainer.html("").append($span.append($table.append($tbody)));
    }
  });
}


function renderArchive(callback) {
  $.ajax({
    type: "GET",
    url: "archive",
    data: {},
    success: function(data) {
      $("#main-container").html(data);
    }
  }).complete(function() {
    if (typeof callback === "function") {
      callback();
    }
  });
}
