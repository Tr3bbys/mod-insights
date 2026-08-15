import { generateStart, FetchMain } from "../data/main.js";

import { loadPlayersFetch, generateSummary, generateWeapons, generateWeaponNotes, generateEntryChart, generateHltvRatings, generateOverallForm, generateByMapTable, generateMatchLog, generateMapPositioning} from "./Summary/summary.js";

import { initSwiper } from "./swiper-initi.js";

import { loadBestPairsFetch, generateBestPairs } from "./Best-Pairs/best-pairs.js";

async function loadPage() {
   try{
      await FetchMain();
      await loadPlayersFetch();
      await loadBestPairsFetch();

   }catch(error){
    console.log('Failed status:' , error)
   }

   generateStart();

   generateSummary();

   generateHltvRatings();
   generateEntryChart();

   generateWeapons();
   initSwiper();
   generateWeaponNotes();

   generateOverallForm();
   generateByMapTable();
   generateMatchLog();

   generateBestPairs();

   generateMapPositioning();
   
}

loadPage();