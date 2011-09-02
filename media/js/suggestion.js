function upvote(pk) {
    $.ajax({
        type: "POST",
        data: ({ 'pk' : pk }),
        url: '/upvote',
        success: function(response){
            if (response == 'already_voted') {alert('You already voted on this suggestion.');}
            else if (response == 'too_many') {alert('You have voted on 10 suggestions, which is the maximum. If you feel more strongly about a particular suggestion, remove a vote from another suggestion.')}
            else if (response != 'ok'){
                alert('Could not upvote successfully');
            }
            else { 
                var id = "#" + pk.toString();
                var old = $(id).html();
                var plus_one = parseInt(old) + 1;
            $(id).html(plus_one.toString());
            }
        },
        error: function(){
           alert('Could not upvote.');
        }
        });   
    return true;
};

