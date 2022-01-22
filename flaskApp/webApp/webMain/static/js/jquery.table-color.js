/********
    
Author: Manoj Prajapat
	
****/

(function($){
   $.fn.tblcolor = function (options) 
   {

	    var btn_font_color = document.createElement("button");
		btn_font_color.onclick = function() { alert("blabla"); };
		btn_font_color.innerHTML = '<i class="fa fa-font"></i>';
		
		
        var html_color_picker = '<div class="tblcolor-picker">'+
		                          '<i class="fa fa-font tblcolor-color"></i>'+
								  '<i class="fa fa-paint-brush tblcolor-bgcolor"></i>'+
		                        '</div>';
								
         return this.each(function()
		 {
              var obj  = $(this);
			  				
			  $(obj).find('td').on('mouseenter', function() 
			  {
				  td = $(this);
				  var exist_td_font_color = tblcolor_rgb2hex(td.css("color"));
				  var exist_td_bg_color = tblcolor_rgb2hex(td.css("background-color"));
				  
				  var html = document.createElement("div");
				  html.setAttribute("class","tblcolor-picker");
				  
				  // for color.
				  var font_color_picker = document.createElement("input");
				  font_color_picker.setAttribute("type","color");
				  font_color_picker.setAttribute("class","tblcolor-col");
				  font_color_picker.setAttribute("value",exist_td_font_color);
				  font_color_picker.onchange = function() { td.css("color",(this.value)); }
				  
				  var color_label = document.createElement("i");
				  color_label.setAttribute("class","fa fa-font");
				  color_label.setAttribute("style","color:#000;position: relative;top: -5px;");
				  color_label.innerHTML=":";
				  
				  // for background.
				   var font_bg_picker = document.createElement("input");
				  font_bg_picker.setAttribute("type","color");
				  font_bg_picker.setAttribute("class","tblcolor-bg");
				  font_bg_picker.setAttribute("value",exist_td_bg_color);
				  font_bg_picker.onchange = function() { td.css("background-color",(this.value)); }
				  
				  var color_bg = document.createElement("i");
				  color_bg.setAttribute("class","fa fa-paint-brush");
				  color_bg.setAttribute("style","color:#000;position: relative;top: -5px;margin: 0px 5px;");
				  color_bg.innerHTML=":";
				  
				  html.appendChild(color_label);
				  html.appendChild(font_color_picker);
				  
				  html.appendChild(color_bg);
				  html.appendChild(font_bg_picker);
			  
			      if(td.find('.tblcolor-picker').length <= 0) { td.append(html);  }
				  
				   
				 $("#triggerSet").spectrum("set", $("#enterAColor").val());
				 
			 });
			 
				
			 $(obj).find('td').on('mouseleave', function() 
			  {
				  
				  td = $(this);
				  if(td.find('.tblcolor-picker').length > 0) td.find('.tblcolor-picker').remove();
			  });
			
			
         });
     };
 
   
})(jQuery);

function tblcolor_rgb2hex(rgb) 
{
    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    if (rgb != null)
    return "#" + tblcolor_hex(rgb[1]) + tblcolor_hex(rgb[2]) + tblcolor_hex(rgb[3]);
}

 function tblcolor_hex(x) {
        return ("0" + parseInt(x).toString(16)).slice(-2);
    }
