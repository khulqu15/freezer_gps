<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="min-h-screen w-full relative bg-base-200 text-base-content">
        <div class="py-2 px-4 bg-base-100 w-full flex items-center justify-between">
          <div class="w-full">
          </div>
          <div class="flex items-center gap-3">
            <button class="btn btn-base-300" @click="$router.push({name: 'Home'})">Monitoring</button>
          </div>
        </div>
        <div class="grid grid-cols-4 min-h-[88vh] items-center justify-items-center">
          <div class="col-span-4 md:col-span-4 p-4 text-left w-full space-y-2">
            <card-view-vue header="Data Table">
              <div class="flex items-center gap-3 mb-6">
                <button class="btn btn-primary" @click="exportToExcel()">Export Excel</button>
                <button class="btn btn-error" @click="deleteAll()">Delete All</button>
              </div>
              <div class="w-full max-h-[60vh] h-[33vh] overflow-auto">
                <table class="table table-sm">
                  <thead>
                    <tr>
                      <th></th>
                      <th>Temperature (C)</th>
                      <th>Location</th>
                      <th>Timestamp</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in tableData" :key="index">
                      <th>{{ index + 1 }}</th>
                      <td>{{ parseInt(item.data.temperature) }} C</td>
                      <td>{{ item.data.location }}</td>
                      <td>{{ item.data.timestamp }}</td>
                      <td>
                        <button @click="deleteByKey(item.key)" class="btn btn-error btn-sm">Delete</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </card-view-vue>
          </div>

          <div class="col-span-4 md:col-span-2 p-4 text-left w-full space-y-2">
            <div v-if="waves.length > 0">
              <card-view-vue header="Chart Plotting">
                <div v-if="selectedWave == -1">
                  <waves-chart-vue 
                    :wave-data="waves.map(wave => wave.data)" 
                    :wave-names="waves.map(wave => wave.name)" 
                  />
                </div>
                <div v-else>
                  <waves-chart-vue 
                    :wave-data="[waves[selectedWave].data]" 
                    :wave-names="[waves[selectedWave].name]" 
                  />
                </div>
              </card-view-vue>
            </div>
          </div>
          
          <div class="col-span-4 md:col-span-2 p-4 w-full">
            <div class="w-full h-[50vh] relative overflow-hidden">
                <div id="map" class="h-[50vh] w-full"></div>
            </div>
          </div>

        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import CardViewVue from '@/components/CardView.vue';
import { IonContent, IonPage } from '@ionic/vue';
import { ref, Ref, onMounted } from 'vue';
import { database, ref as firebaseRef, get } from '@/firebaseConfig';
import { remove, child } from 'firebase/database';
import WavesChartVue from '@/components/WavesChart.vue';
import * as XLSX from 'xlsx'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css';

const selectedWave: Ref<any> = ref(-1);
const tableData: Ref<any> = ref([])

onMounted(() => {
  fetchDataFromFirebase();
  document.documentElement.setAttribute('data-theme', 'garden')
  let testData = encryptText('{ "location": "-7.269376, 112.782494", "temperature": 5.5, "timestamp": "10/12/2024 20:25" }')
  console.log(testData)
});

function decryptText(encryptedText: string) {
  let decryptedText = ""
  let decrypted = '';
  const key = "rio"
  const keyLength = key.length
  try {
    for (let i = 0; i < encryptedText.length; i++) {
      const encryptedCharCode = encryptedText.charCodeAt(i)
      const keyCharCode = key.charCodeAt(i % keyLength)
      const decryptedCharCode = encryptedCharCode - keyCharCode
      decrypted += String.fromCharCode(decryptedCharCode)
    }
    decryptedText = decrypted;
  } catch (error) {
    console.error('Error decrypting text:', error);
  }
  return decryptedText
}

function encryptText(plainText: string) {
  let encryptedText = '';
  const key = "rio";
  const keyLength = key.length;

  try {
    for (let i = 0; i < plainText.length; i++) {
      const plainCharCode = plainText.charCodeAt(i);
      const keyCharCode = key.charCodeAt(i % keyLength);
      const encryptedCharCode = plainCharCode + keyCharCode;
      encryptedText += String.fromCharCode(encryptedCharCode);
    }
  } catch (error) {
    console.error('Error encrypting text:', error);
  }
  return encryptedText;
}


async function fetchDataFromFirebase() {
  try {
    const snapshot = await get(firebaseRef(database, 'freezer_data/'));
    if (snapshot.exists()) {
      const data = snapshot.val();
      console.log(data)
      tableData.value = Object.entries(data).map(([key, value]: any) => ({
        key,
        data: JSON.parse(decryptText(value)), // location: "-7.273921, 112.802100", temperature: 24.23, timestamp: "20/03/2024 12:32"
      }));

      console.log(tableData.value)

      // sort data by timestamp
      tableData.value.sort((a: any, b: any) => {
        const [dateA, timeA] = a.data.timestamp.split(" ");
        const [dayA, monthA, yearA] = dateA.split("/");
        const [hourA, minuteA] = timeA.split(":");
        const dateObjA = new Date(`${yearA}-${monthA}-${dayA}T${hourA}:${minuteA}:00`);

        const [dateB, timeB] = b.data.timestamp.split(" ");
        const [dayB, monthB, yearB] = dateB.split("/");
        const [hourB, minuteB] = timeB.split(":");
        const dateObjB = new Date(`${yearB}-${monthB}-${dayB}T${hourB}:${minuteB}:00`);

        return dateObjA.getTime() - dateObjB.getTime();
      });

      const temperatures: any = [];
      const waypoints: any = [];

      tableData.value.forEach((el: any, index: number)=> {
        const [datePart, timePart] = el.data.timestamp.split(" ");
        const [day, month, year] = datePart.split("/");
        const formattedDate = `${year}-${month}-${day}T${timePart}:00`;
        const date = new Date(formattedDate);
        if (!isNaN(date.getTime())) {
          temperatures.push({
            value: el.data.temperature,
            date: formattedDate
          })
        }
        console.log(temperatures)

        const [lat, lng] = el.data.location.split(',').map(Number);
        if (!isNaN(lat) && !isNaN(lng)) {
          waypoints.push({ lat, lng });
        }
      });

      waves.value[0].data = temperatures;
      if (waypoints.length > 0) {
        plotWaypointsOnMap(waypoints);
      }
    } else {
      console.log("No data available");
    }
  } catch (error) {
    console.error("Error fetching data from Firebase:", error);
  }
}

const waves = ref([
  { name: 'Temperatures', data: [] as { value: number; date: string }[] },
]);

function plotWaypointsOnMap(waypoints: { lat: number; lng: number }[]) {
  const map = L.map('map').setView([waypoints[0].lat, waypoints[0].lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  const latlngs: any = waypoints.map(point => [point.lat, point.lng]);
  waypoints.forEach(point => {
    L.marker([point.lat, point.lng]).addTo(map);
  });

  L.polyline(latlngs, { color: 'blue' }).addTo(map);
}


async function deleteByKey(key: string) {
  try {
    await remove(firebaseRef(database, `freezer_data/${key}`));
    tableData.value = tableData.value.filter((item: any) => item.key !== key);
    console.log(`Entry with key ${key} deleted successfully`);
  } catch (error) {
    console.error(`Error deleting entry with key ${key}:`, error);
  }
}

async function deleteAll() {
  try {
    await remove(firebaseRef(database, 'freezer_data'));
    tableData.value = [];
    console.log("All entries deleted successfully");
  } catch (error) {
    console.error("Error deleting all entries:", error);
  }
}

function exportToExcel() {
  const waveData = waves.value.map(wave => {
    return {
      name: wave.name,
      data: wave.data.map(point => ({
        value: point.value,
        date: point.date
      }))
    };
  });

  const waveSheet = XLSX.utils.json_to_sheet(
    waveData.flatMap(wave => wave.data.map((point, index) => ({
      Name: wave.name,
      Value: point.value,
      Date: point.date,
      Index: index + 1
    })))
  );

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, waveSheet, 'Waves');
  XLSX.writeFile(workbook, 'WaveData.xlsx');
}

</script>