

inprog=[];
queued=[];
function mark_notam(notam,line)
{
    if (inprog.length>0)
    {
        queued.push([notam,line]);
        return;
    }
    inprog
}
function click_item(notam,line,already_toggled)
{
    if (already_toggled==0)
    {
        var e=document.getElementById('notam_'+notam+'_'+line);
        if (e.checked)
            e.checked=undefined;
        else
            e.checked='1';
    }
}
