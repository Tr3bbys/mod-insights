export let main_text;

export async function FetchMain() {
    const promise = fetch('report_data.json')
        .then((response) => response.json())
        .then((textData) => {
            main_text = new Main(textData.report_meta);
        })
        .catch((error) => {
            console.log('Failed with status:', error);
        });

    return promise;
}



export class Main {
    version;
    date;
    weekly_focus;

    constructor(textDetails) {
        this.version = textDetails.version;
        this.date = textDetails.date;
        this.weekly_focus = textDetails.weekly_focus;
    }

}

export function generateStart() {

    let generateHTML = '';



    generateHTML += `
            <div class="top-section">
                <div class="top-section-text">
                    <p class="text-sub-head">Weekly squad report - ${main_text.version}</p>
                    <p class="text-header">CS-GO Insights</p>
                    <p class="text-sub-head">${main_text.date} - Compiled from Leefity & HLTV match data</p>
                </div>

                <div class="MOD-img-container">
                    <img class="MOD-img" src="cs-go-tracker-project-main/images/logos/MOD_insights_group-logo.jpeg">
                </div>
            </div>

            <div class="bottom-section">
                <div class="bottom-section-text">
                    <p class="bottom-text-header">This week's Focus</p>
                    <p class="bottom-sub-text">${main_text.weekly_focus}</p>
                </div>
            </div>
        `;




    document.getElementById('js-main-container').innerHTML = generateHTML;
}