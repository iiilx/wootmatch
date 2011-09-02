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

function showDelete() {
    $("#tos").hide();
    $("#privacy").hide();
    $("#delete-account").show();
};

function updateRanks() {
    var dataz = '';
    var tbl_len = $('tr').length + 1;
    for(var i=1; i < tbl_len; i++) { 
        dataz += $("tbody tr:nth-child("+ i.toString() +")").attr("id") + '.';
    }
    $.ajax({
        type: "POST",
        data: ({ 'rank_order' : dataz.replace('undefined.','') }),
        url: '/update-rank',
        success: function(response){
            reorder();
        },
        error: function(){ 
            //fix rows again to original...
            alert('could not update ranks');
        }
    });
}

function showPrivacy() {
    $("#delete-account").hide();
    $("#tos").hide();
    $("#privacy").show("fast");
}


function showTos() {
    $("#delete-account").hide();
    $("#privacy").hide();
    $("#tos").show("fast");
}

function updateNumber(num) {
    var ppl = ' people';
    if (num == 1) { ppl = ' person'; }
    if (num == -1) { num = 0; }
    $("#num_likes").html(num.toString() + ppl);
};

function reorder() {
    curr_len = $('tr').length + 1;
    for(var i=1; i < curr_len; i++) {
        $('tbody tr:nth-child(' + i.toString() + ') td:nth-child(2)').html(i.toString());
    };  
};

function removePerson(uid) {
    $.ajax({
        type: "POST",
        data: ({ 'remove' : uid }),
        url: '/remove-person',
        success: function(response){
            $('#'+uid).remove();                  
            $("#rank").val($('tr').length + 1).toString();
            reorder();         
            updateRanks();
            updateNumber($('tr').length);
        },
        error: function(){ alert('could not remove person');}
  });
};

function changeValue(){
    if(document.getElementById("example").value != ""){
        var name = document.getElementById("example").value;
        var uid = window.fids[window.globaldata.indexOf(name)];
        if (typeof uid != "string" || uid == '') {
            alert('Please refresh the page or reselect someone.');
            return false;
        }
        var rowId = '#'+uid;
        if ($(rowId).length > 0) {
            alert('You already like that person!');
            return false;
        }
        else { 
            document.getElementById("add_like_uid").value = uid;
            document.getElementById("add_like_name").value = name;
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

