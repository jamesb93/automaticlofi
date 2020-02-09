pythonlocation = '/usr/local/bin/python3',
scriptlocation = '/Users/macbook/Documents/Code/GitHub_repos/automaticlofi/youtube_rip/youtubeRip.py',
numsamples     = '1',
query          = 'lounge jazz chill',
textcheck      = 'False',
output         = '/Users/macbook/Documents/Code/GitHub_repos/automaticlofi',
recursive      = 'True',
iterations     = '1',
maxlen         = '20',
numpages       = '1';

setoutletassist(0, '(String) Command Out');
setinletassist(0, '(String) Settings In');

function bang(){
    outputstring();
}

function outputstring(){
    outString = pythonlocation + ' ' + scriptlocation + ' ';
    outString = outString + '-n '  + numsamples + ' ';
    outString = outString + '-q "' + query + '" ';
    outString = outString + '-t '  + textcheck + ' ';
    outString = outString + '-o "' + output + '" ';
    outString = outString + '-r '  + recursive + ' ';
    outString = outString + '-i '  + iterations + ' ';
    outString = outString + '-m '  + maxlen + ' ';
    outString = outString + '-p '  + numpages;
    outlet(0, outString);
}

function setpythonlocation(txt){
    pythonlocation = txt;
}

function setscriptlocation(txt){
    scriptlocation = txt;
}

function setnumsamples(txt){
    numsamples = String(txt);
}

function setquery(list){
    query = '';
    for(i = 0; i < arguments.length; i++){
        query = query + String(arguments[i])
        if(i != arguments.length - 1)
            query = query + ' '
    }
}

function settextcheck(txt){
    textcheck = txt;
}

function setoutput(txt){
    output = txt;
}

function setrecursive(txt){
    recursive = txt;
}

function setiterations(txt){
    iterations = String(txt);
}

function setmaxlen(txt){
    maxlen = String(txt);
}

function setnumpages(txt){
    numpages = String(txt);
}