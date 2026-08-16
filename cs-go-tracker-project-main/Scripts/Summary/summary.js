
const WEAPON_IMAGES = {
    "AK47": "cs-go-tracker-project-main/images/weapons/AK-47.webp",
    "M4A4": "cs-go-tracker-project-main/images/weapons/M4A4.webp",
    "M4A1-S": "cs-go-tracker-project-main/images/weapons/M4A1-S.webp",
};

const TIER_CLASS = { high: "high-confidence", med: "med-confidence", low: "low-confidence" };
const TIER_LABEL = { high: "High", med: "Medium", low: "Low" };

let players = [];

let weapon_note = [];

let chart_data = {};

let recent_form =  {};

let maps_data = [];

let overpass_data = {};

export function loadPlayersFetch() {


    const promise = fetch('report_data.json').then((response) => {
        return response.json()

    }).then((playersData) => {
        players = playersData.players.map((playerDetails) =>  new Player_weapons(playerDetails));
        weapon_note = playersData.players.map((playerDetails) => new WeaponText(playerDetails));

        chart_data = playersData.chart_data;

        recent_form = playersData.recent_form

        maps_data = playersData.maps;

        overpass_data = playersData.overpass;

    }).catch((error) => {
        console.log('Failed with status:', error);
    });

    return promise;
}



export class Players {
    avatar;
    name;
    role;
    games;
    tier;
    ct_detail;
    t_detail;
    good;
    note;


    constructor(playerDetails) {
        this.avatar = playerDetails.avatar;
        this.name = playerDetails.name;
        this.role = playerDetails.role;
        this.games = playerDetails.games;
        this.tier = playerDetails.tier;
        this.ct_detail = playerDetails.ct_detail;
        this.t_detail = playerDetails.t_detail;
        this.good = playerDetails.good
        this.note = playerDetails.note;
    }
}


export function generateSummary () {
    let generateHTML = '';


    players.forEach((playerDetails) => {
        generateHTML += 
        `<div class="summary-container">

               <div class="summary-left-section">
                        <div class="summary-img-container">
                            <img class="profile-img" src="${playerDetails.avatar}">
                        </div>

                        <div class="summary-text-container">
                            <p class="profile-name"> ${playerDetails.name} </p>
                            <p class="summary-text"> Role: <span class="bold-text">${playerDetails.role}</span> </p>
                            <p class="summary-text"> Games: <span class="bold-text">${playerDetails.games}</span></p>
                            <p class="summary-text"> Confidence: </p>

                            <button class="${TIER_CLASS[playerDetails.tier] || "med-confidence"}"> ${TIER_LABEL[playerDetails.tier] || playerDetails.tier} </button>
                        </div>
                    </div>

                    <div class="summary-right-section">
                        <div class="ct-section">
                            <div class=" ct-img-and-text">
                                <p class="CT"> CT </p>
                                <img class="CT-logo" src="cs-go-tracker-project-main/images/logos/Ct_logo.webp">
                            </div>

                            <div class="ct-text">
                                <span>${playerDetails.ct_detail}</span>
                            </div>
                        </div>

                        <div class="t-section">
                            <div class="t-img-and-text">
                                <p class="T"> T </p>
                                <img class="T-logo" src="cs-go-tracker-project-main/images/logos/T_logo.webp">
                            </div>

                            <div class="t-text">
                                <span>${playerDetails.t_detail}</span>
                            </div>
                        </div>

                        <div class="pos-neg-container">
                            <div class="pos-flex">
                                <i class="ri-add-fill pos-icon"></i>
                                <div class="pos">
                                    <span>${playerDetails.good}</span>
                                </div>
                            </div>

                            <div class="neg-flex">
                                <i class="ri-subtract-fill neg-icon"></i>
                                <div class="neg">
                                    <span>${playerDetails.note}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                 </div>`
    })

    document.getElementById('js-summary-container').innerHTML = generateHTML
}



class Player_weapons extends Players {
    best_t_weapon;
    best_t_weapon_img;
    best_t_hs;
    best_ct_weapon;
    best_ct_weapon_img;
    best_ct_hs;


    constructor(playerDetails) {
        super(playerDetails);

        this.best_t_weapon = playerDetails.best_t_weapon;
        this.best_t_weapon_img = WEAPON_IMAGES[playerDetails.best_t_weapon] || "";
        this.best_t_hs = playerDetails.best_t_hs;
        this.best_ct_weapon = playerDetails.best_ct_weapon;
        this.best_ct_weapon_img = WEAPON_IMAGES[playerDetails.best_ct_weapon] || "";
        this.best_ct_hs = playerDetails.best_ct_hs;

    }
}


export function generateWeapons () {

    let generateHTML = '';

    players.forEach((playerDetails) => {
        generateHTML += 
         `<div class="swiper-slide">
                        <div class="weapon-main-top-container">
                            <div class="weapon-image-container">
                                <img class="weapons-profile-image"
                                    src="${playerDetails.avatar}">
                            </div>

                            <div class="weapon-profile-name-container">
                                <span class="weapon-profile-name">${playerDetails.name}</span>
                            </div>
                        </div>

                        <div class="weapon-main-bottom-container">
                            <div class="weapon-container-1">
                                <div class="weapon-title">
                                    <span class="weapon-CT">Best CT Weapon</span>
                                </div>

                                <div class="weapon-image">
                                    <img class="weapon" src="${playerDetails.best_ct_weapon_img}">
                                    <span class="weapon-name">${playerDetails.best_ct_weapon}</span>
                                </div>

                                <div class="headshot-container">
                                    <span class="headshot-percentage">HS: ${playerDetails.best_ct_hs}</span>
                                </div>
                            </div>

                            <div class="weapon-container-1">
                                <div class="weapon-title">
                                    <span class="weapon-T">Best T Weapon</span>
                                </div>

                                <div class="weapon-image">
                                    <img class="weapon" src="${playerDetails.best_t_weapon_img}">
                                    <span class="weapon-name">${playerDetails.best_t_weapon}</span>
                                </div>

                                <div class="headshot-container">
                                    <span class="headshot-percentage">HS: ${playerDetails.best_t_hs}</span>
                                </div>
                            </div>
                        </div>
                    </div>`
    })

    document.getElementById('js-swiper-wrapper').innerHTML = generateHTML;
}


class WeaponText extends Players{
    
    weapon_note;

    constructor(playerDetails){
        super(playerDetails)

        this.weapon_note = playerDetails.weapon_note;
    }
}


export function generateWeaponNotes (){

    let generateHTML = '' ;

    weapon_note.forEach((note) => {
        generateHTML += `<div class="weapon-summary-container">
                    <div class="weapon-summary-text">
                        <span class="profile-summary-name">${note.name}:</span>
                        <span>${note.weapon_note}</span>
                    </div>
                </div>`
    })


    document.getElementById('js-weapon-summary-summary-container').innerHTML = generateHTML;
}


export function generateHltvRatings() {
    let generateHTML = '';

    Object.entries(chart_data.hltv_rating).forEach(([playerName, rating]) => {
        const barHeight = (rating / 1.5) * 100;

        generateHTML += `
            <div class="chart-group">
                <div class="bar bar-orange" style="--bar-height: ${barHeight}%;">
                    <span class="bar-value">${rating}</span>
                </div>
                <span class="x-label">${playerName}</span>
            </div>
        `;
    });

    document.querySelector('.chart-card:nth-child(1) .chart-grid').innerHTML = generateHTML;
}

export function generateEntryChart() {
    let generateHTML = '';

    Object.keys(chart_data.ct_entry_success).forEach((playerName) => {
        const ctValue = chart_data.ct_entry_success[playerName];
        const tValue = chart_data.t_entry_success[playerName];

        const ctHeight = (ctValue / 70) * 100;
        const tHeight = (tValue / 70) * 100;

        generateHTML += `
            <div class="chart-group">
                <div class="bar bar-blue" style="--bar-height: ${ctHeight}%;">
                    <span class="bar-value">${ctValue}%</span>
                </div>
                <div class="bar bar-orange" style="--bar-height: ${tHeight}%;">
                    <span class="bar-value">${tValue}%</span>
                </div>
                <span class="x-label">${playerName}</span>
            </div>
        `;
    });

    document.querySelector('.chart-card:nth-child(2) .chart-grid').innerHTML = generateHTML;
}


export function generateOverallForm() {
    const { wins, losses, win_rate } = recent_form.overall;
    const totalGames = wins + losses;

    document.getElementById('js-form-result').innerHTML = `
        <span class="result">${wins}-${losses}</span> Last ${totalGames} games. ${win_rate}% win rate
    `;

    document.getElementById('js-form-note').textContent = `${recent_form.mode} - ${recent_form.note}`;
}

export function generateByMapTable() {
    let generateHTML = '';

    Object.entries(recent_form.by_map).forEach(([mapName, stats]) => {
        generateHTML += `
            <tr>
                <td class="map-name">${mapName}</td>
                <td>${stats.w}-${stats.l}</td>
                <td>${stats.win_rate}%</td>
                <td>${stats.games}</td>
            </tr>
        `;
    });

    document.getElementById('js-by-map-body').innerHTML = generateHTML;
}

export function generateMatchLog() {
    let generateHTML = '';

    recent_form.matches.forEach((match) => {
        const resultClass = match.result === 'W' ? 'win' : 'lose';

        generateHTML += `
            <tr>
                <td>${match.date}</td>
                <td>${match.map}</td>
                <td>${match.us} : ${match.them}</td>
                <td><span class="result-badge ${resultClass}">${match.result}</span></td>
            </tr>
        `;
    });

    document.getElementById('js-match-log-body').innerHTML = generateHTML;
}

function parsePositionEntry(entry) {
    const separatorIndex = entry.indexOf(' - ');
    const name = entry.slice(0, separatorIndex);
    const description = entry.slice(separatorIndex + 3); // +3 skips " - "
    return { name, description };
}


export function generateMapPositioning() {
    let generateHTML = '';

    maps_data.forEach((map, index) => {
        const slug = map.name.toLowerCase().replace(/\s+/g, '-'); // "Dust II" -> "dust-ii"
        const activeClass = index === 0 ? 'active-4' : '';

        const ctItems = map.ct.map((entry) => {
            const { name, description } = parsePositionEntry(entry);
            return `<li><span class="profile-name-2">${name}</span> - ${description}</li>`;
        }).join('');

        const tItems = map.t.map((entry) => {
            const { name, description } = parsePositionEntry(entry);
            return `<li><span class="profile-name-2">${name}</span> - ${description}</li>`;
        }).join('');

        const noteHTML = map.note
            ? `<div class="sub-p">${map.note}</div>`
            : '';

        generateHTML += `
            <div class="map-positioning-container ${activeClass}" data-map="${slug}">
                <div class="map">
                    <span class="map-name">${map.name}</span>
                </div>

                <div class="both-sides-container">
                    <div class="map-left-section">
                        <div class="CT-side">
                            <img class="CT-logo logo" src="cs-go-tracker-project-main/images/logos/Ct_logo.webp">
                            <span class="CT-title">CT Side</span>
                        </div>
                        <ul class="side-tasks">${ctItems}</ul>
                    </div>

                    <div class="map-right-section">
                        <div class="T-side">
                            <img class="T-logo logo" src="cs-go-tracker-project-main/images/logos/T_logo.webp">
                            <span class="T-title">T Side</span>
                        </div>
                        <ul class="side-tasks">${tItems}</ul>
                    </div>
                </div>

                ${noteHTML}
            </div>
        `;
    });

    document.querySelector('.map-flex-buttons').insertAdjacentHTML('afterend', generateHTML);
}