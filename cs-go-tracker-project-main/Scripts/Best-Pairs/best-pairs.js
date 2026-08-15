let best_pairs = [];


export function loadBestPairsFetch(){
    const promise = fetch('report_data.json').then((response) => {
        return response.json()

    }).then((pairsData) => {
        best_pairs = pairsData.best_pairs.map((pairsDetails) => new Pairs(pairsDetails) )
    }).catch((error) => {
        console.log('Failed with status:', error);
    });

    return promise;
    
}



export class Pairs{
    title;
    players;
    reasoning;

    constructor(pairsDetails){
        this.title = pairsDetails.title;
        this.players  = pairsDetails.players;
        this.reasoning = pairsDetails.reasoning;
    }
}


export function generateBestPairs () {
    let generateHTML = '';

    best_pairs.forEach((pair) => {
        generateHTML += `<div class="best-pair-container">
                    <div class="best-text-container">
                        <div class="title-divider">
                            <span class="best-title"> ${pair.title}</span>
                        </div>

                        <div class="name-divider">
                            <span class="best-profile-names">${pair.players}</span>
                        </div>

                        <div class="paragraph-divider">
                            <P>${pair.reasoning}</P>
                        </div>
                    </div>
                </div>`;
    })


    document.getElementById('js-best-pair-main-container').innerHTML = generateHTML;
}