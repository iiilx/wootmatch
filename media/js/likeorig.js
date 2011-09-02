$('html').ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});


function changeValue(){
    if(document.getElementById("example").value != ""){
        //alert(window.fids[window.globaldata.indexOf(document.getElementById("example").value)]);
        //return false;
        var uid = window.fids[window.globaldata.indexOf(document.getElementById("example").value)];
        if (typeof uid == "undefined") {
            alert('Please refresh the page or reselect someone.');
            return false;
        }
        else { document.getElementById("intz").value = uid;
            return true;
        }
    }
    else {
        alert('You must select someone to like!');
        return false;
    }
};

function showEmail() {
//    $("#change_email").show(); //fadeIn("fast");
    document.getElementById("change_email").style.display = 'inline';
    document.getElementById("old_email").style.display = 'none';
//    $("#old_email").hide();
};

function validEmail() {
    if (document.getElementById("new_email").value != '') {return true;}
    else {
         alert('Enter a valid e-mail address please.');
         return false;
    }
}
function update_matches() {
$.ajax({
    type: "POST",
    dataType: 'json',
    url: '/update-matches',
    success: function(json){
        var matches='';
        var len = window.likeslist.length;
        if(json['matches'].length > 0) {
            for(var i=0; i<len; i++){ //likeslist is an array of integers, matches is an aray of strings
               if ( json['matches'].indexOf(window.likeslist[i].toString()) >= 0 ) {
                    $("tbody tr:nth-child(" + eval(i+1).toString() + ") td:nth-child(2)").html('<span style="color:#4fa936">Yes!</span>');
                }
                else {
                    $("tbody tr:nth-child(" + eval(i+1).toString() + ") td:nth-child(2)").html("No");
                }
            }
        }
        else { $("tbody tr td:nth-child(2)").html("No Match") }

        document.getElementById("last_update").innerHTML = 'just now';
        if(json['has_app'].length > 0) {
            for(var i=0; i < len; i++){
                if( json['has_app'].indexOf(window.likeslist[i].toString()) >= 0 ) {
                   $("tbody tr:nth-child(" + eval(i+1).toString() + ") td:nth-child(3)").html("Yes"); 
                }
                else {
                    $("tbody tr:nth-child(" + eval(i+1).toString() + ") td:nth-child(3)").html("No"); }
            }

/*            for(i in json['has_app']) { 
                alert(json['has_app'][i]);
            }
  */     
        }
        else {
            $("tbody tr td:nth-child(3)").html("No");
            $("#promote").show();
         }
        
    },
    error: function() { alert("error"); }
    });
 };

function tellPeople() {
  FB.ui({
    method: 'stream.publish',
    attachment: {
      name: 'Find out if the person you like likes you back!',
      caption: "This is perfect if you don't want to potentially ruin any friendships.",
      media: [{
        type: 'image',
        href: 'http://apps.facebook.com/likeeachother',
        src: 'http://likeeachother.iiilx.com/media/images/heart.png'
      }]
    },
    action_links: [{
      text: 'Get the app to see if anyone you like likes you too.',
      href: 'http://apps.facebook.com/likeeachother'
    }],
    user_message_prompt: 'Tell your friends about LikeEachOther (optional):'
  });
};

