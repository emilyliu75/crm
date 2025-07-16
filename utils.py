import html



def plaintext_to_html(text):
    safe_text = html.escape(text)
    # Turn double newlines into paragraphs
    safe_text = safe_text.replace('\n\n', '</p><p>')
    # Single newlines become <br>
    safe_text = safe_text.replace('\n', '<br>')
    return f'<p>{safe_text}</p>'

EMAIL_SIGNATURE = """
<div style="font-family: Arial, Helvetica, sans-serif; color: #000001;">
<table style="width: 281px;">
<tbody>
<tr style="height: 31px;">
<td style="width: 281px; height: 40px;">Kind Regards</td>
</tr>
</tbody>
</table>
</div>
<table border="0" width="500" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td style="padding: 0 9px 0 0; vertical-align: top;" valign="top" width="85"><a href="https://www.divi-design.co.uk" target="_blank" rel="noopener"><img style="width: 85px; moz-border-radius: 0%; khtml-border-radius: 0%; o-border-radius: 0%; webkit-border-radius: 0%; ms-border-radius: 0%; border-radius: 0%;" src="https://i.imgur.com/iDBdCrV.png" alt="Divi-Design" width="85" /></a></td>
<td style="border-left: 2px solid; vertical-align: top; border-color: #0F75BC; padding: 0 0 0 9px;" valign="top">
<table style="line-height: 1.4; font-family: Arial, Helvetica, sans-serif; font-size: 96%; color: #000001;" border="0" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td><span style="font: 1.2em Arial, Helvetica, sans-serif; color: #0f75bc;">Divi Design</span> <span style="font-family: Arial, Helvetica, sans-serif; color: #000001;">&nbsp;&nbsp;</span></td>
</tr>
<tr>
<td style="padding: 5px 0;">
<div style="font-family: Arial, Helvetica, sans-serif; color: #000001;">Architectural Services</div>
</td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">p:&nbsp;</span> <a style="text-decoration: none; font-family: Arial, Helvetica, sans-serif; color: #000001;" href="tel:0203 488 2828">0203 488 2828</a></td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">w:&nbsp;</span> <span style="font-family: Arial, Helvetica, sans-serif;"><a style="text-decoration: none; color: #000001;" href="http://www.divi-design.co.uk" target="_blank" rel="noopener">www.divi-design.co.uk</a></span></td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">e:&nbsp;</span> <a style="text-decoration: none; font-family: Arial, Helvetica, sans-serif; color: #000001;" href="mailto:info@divi-design.co.uk" target="_blank" rel="noopener">info@divi-design.co.uk</a></td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">a:&nbsp;</span> <span style="font-family: Arial, Helvetica, sans-serif; color: #000001;">124 City Road, EC1V 2NX&nbsp;</span></td>
</tr>
<tr>
<td style="color: #000001; padding: 8px 0 3px 0; display: block;">&nbsp;</td>
</tr>
<tr>
<td>
<table border="0" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td style="font-family: Arial; padding: 0 4px 0 0;"><a class="sc-hzDkRC kpsoyz" style="display: inline-block; padding: 0px; background-color: #0f75bc;" href="https://twitter.com/Divi_Design"><img class="sc-bRBYWo ccSRck" style="background-color: #0f75bc; max-width: 135px; display: block;" src="https://cdn2.hubspot.net/hubfs/53/tools/email-signature-generator/icons/twitter-icon-2x.png" alt="twitter" height="23" /></a></td>
<td style="font-family: Arial; padding: 0 4px 0 0;"><a class="sc-hzDkRC kpsoyz" style="display: inline-block; padding: 0px; background-color: #0f75bc;" href="https://www.instagram.com/divi_design_architecture/"><img class="sc-bRBYWo ccSRck" style="background-color: #0f75bc; max-width: 135px; display: block;" src="https://cdn2.hubspot.net/hubfs/53/tools/email-signature-generator/icons/instagram-icon-2x.png" alt="instagram" height="23" /></a></td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table border="0" width="500" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td class="s_pixel" colspan="2">&nbsp;</td>
</tr>
<tr>
<td style="line-height: 1px;">&nbsp;</td>
</tr>
</tbody>
</table>
"""


