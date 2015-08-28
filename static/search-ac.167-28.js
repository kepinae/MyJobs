$(document).ready(function(){
    $.ui.autocomplete.prototype._renderItem = function( ul, item){
        /**
        Add syntax highlighting to autocomplete results.
        
        Inputs:
        :ul:    the autocomplete object to modify
        :item:  the individual item to modify
        
        Returns:
        Modified item
        
        **/
        var term = this.term;
        if((term.charAt(0)=='"' && term.charAt(term.length-1) == '"')){
            term = this.term.substr(1,term.length-2);
        }else{
            term = this.term.split(' ').join('|');
        }
        var re = new RegExp("(" + term + ")", "gi") ;      
        var t = item.label.replace(re,"<b class='ac-highlight'>$1</b>");
        return $( "<li></li>" )
            .data( "item.autocomplete", item )
            .append( "<a>" + t + "</a>" )
            .appendTo( ul );
    };
    $("#standardSearch input[type=text]").bind("autocompleteselect", function(event, ul) {
        /**
        When a an autocomplete suggestion is selected, submit the search form
        if location and title fields have a value in them.

        This applies to the MOC, Location, and Title fields on the
        standardSearch form.

        Inputs:
        :event: The autocompleteselect event
        :ul: The autocomplete object (an unordered list)

        Returns:
        Nothing (but does submit search form if both fields have values)

         **/
        $(this).val(ul.item.value);
        if ($('#moc').length > 0) {
            if ($('#location').val() != "" && $('#q').val() != "" && $('#moc').val() != "") {
               $("#standardSearch").submit();
            }
        }
        else {
            if ($('#location').val() != "" && $('#q').val() != "") {
               $("#standardSearch").submit();
            }
        }
    });
	$( ".micrositeLocationField" ).autocomplete({
		/**
		Add autocomplete functionality to the Where search field.
		
		**/
		source: function( request, response ) {
			$.ajax({
				url: "/ajax/ac/?lookup=location&term="+request.term,
				dataType: "jsonp",
				success: function( data ) {
					//alert(data[1].label);
					response( $.map( data, function( item ) {
						return {
							label: item.location + " - (" + item.jobcount + ")",
							value: item.location
						};
					}));
				}
			});                   
		},
        open: function(event, ul) {
            $(".ui-autocomplete li.ui-menu-item:odd").addClass("ui-menu-item-alternate");
        },
		minLength: 2
	});    
	$( ".micrositeTitleField" ).autocomplete({
	    /**
		Add autocomplete functionality to the What search field.
		
		**/
		source: function( request, response ) {
			$.ajax({
				url: "/ajax/ac/?lookup=title&term="+request.term,
				dataType: "jsonp",
				success: function( data ) {
					response( $.map( data, function( item ) {
						return {
                            // Removing numbers to avoid confusion for now
							label: item.title,
							value: item.title
						};
					}));
				}
			});                   
		},
        open: function(event, ul) {
            $(".ui-autocomplete li.ui-menu-item:odd").addClass("ui-menu-item-alternate");
            $(".ui-autocomplete li.ui-menu-item a").removeClass("ui-corner-all");
        },
		minLength: 2,
        select: function(event, ul) {
            event.preventDefault();
            $(this).val('"' + ul.item.label + '"');
        }
	});
    $( ".micrositeMOCField" ).autocomplete({   
        /**
		Add autocomplete functionality to the MOC/MOS search field.
		
		**/
        source: function( request, response ) {
            $.ajax({
                url: "/ajax/mac/?lookup=moc&term="+request.term,
                dataType: "jsonp",
                success: function( data ) {
                    response( $.map( data, function( item ) {
                        return {
                            label: item.label,
                            value: item.value,
	                        moc_id: item.moc_id
                        };
                    }));
                }
            });
        },
	    select: function( event, ui ) {
		    $( "#moc_id" ).val(ui.item.moc_id);
	    },
        open: function(event, ul) {
            $(".ui-autocomplete li.ui-menu-item:odd").addClass("ui-menu-item-alternate");
        },
        minLength: 2
    });
    $( "#moc" ).change(function (event) {
        //Clear moc_id value if moc is changed
            $( "#moc_id" ).val("");
    });
});
