/***************************/
//@Author: Adrian "yEnS" Mato Gondelle & Ivan Guardado Castro
//@website: www.yensdesign.com
//@email: yensamg@gmail.com
//@license: Feel free to use it, but keep this credits please!					
/***************************/

$(document).ready(function(){
	$(".tabs > span").click(function(e){
		switch(e.target.id){
			case "t1":
				//change status & style menu
				$("#t1").addClass("active");
				$("#t2").removeClass("active");
				$("#t3").removeClass("active");
				//display selected division, hide others
				$("div.t1").fadeIn();
				$("div.t2").css("display", "none");
				$("div.t3").css("display", "none");
			break;
			case "t2":
				//change status & style menu
				$("#t1").removeClass("active");
				$("#t2").addClass("active");
				$("#t3").removeClass("active");
				//display selected division, hide others
				$("div.t2").fadeIn();
				$("div.t1").css("display", "none");
				$("div.t3").css("display", "none");
			break;
			case "t3":
				//change status & style menu
				$("#t1").removeClass("active");
				$("#t2").removeClass("active");
				$("#t3").addClass("active");
				//display selected division, hide others
				$("div.t3").fadeIn();
				$("div.t2").css("display", "none");
				$("div.t1").css("display", "none");
			break;
		}
		//alert(e.target.id);
		return false;
	});
});
