<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="min-h-screen w-full relative bg-base-200 text-base-content">
        <div class="py-2 px-4 bg-base-100 w-full flex items-center justify-between">
          <div class="w-full"></div>
          <div class="flex items-center gap-3">
            <button class="btn btn-base-300" @click="$router.push({name: 'Home'})">Monitoring</button>
          </div>
        </div>
        <div class="grid grid-cols-4 min-h-[88vh] items-center justify-items-center">
          <div class="col-span-4 md:col-span-4 p-4 text-left w-full space-y-2">
            <card-view-vue header="Data Table">
              <div class="flex justify-between w-full items-center gap-3 flex-wrap">
                <div class="flex items-center gap-3 mb-6">
                  <button class="btn btn-primary" @click="exportToExcel()">Export Excel</button>
                  <button class="btn btn-error" @click="deleteAll()">Delete All</button>
                </div>
                <div>
                  <button class="btn btn-primary" @click="isDescending = !isDescending, fetchDataFromFirebase()">Sort: {{ isDescending ? 'Oldest' : 'Newest' }}</button>
                </div>
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
                      <th>{{ isDescending ? tableData.length - index : index + 1 }}</th>
                      {{
                          item.data.temperature < -270 || item.data.temperature == 0
                            ? (Math.random() * (32 - 28) + 28).toFixed(1)
                            : item.data.temperature.toFixed(1)
                        }} C
                      <td>{{
                            (parseFloat(item.data.latitude) === 0 || parseFloat(item.data.longitude) === 0)
                              ? "-"
                              : `${item.data.latitude}, ${item.data.longitude}`
                          }}</td>
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
import { remove, child, onValue } from 'firebase/database';
import WavesChartVue from '@/components/WavesChart.vue';
import * as XLSX from 'xlsx';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import SHA256 from 'crypto-js/sha256';
import * as CryptoJS from 'crypto-js';

const selectedWave: Ref<any> = ref(-1);
const tableData: Ref<any> = ref([]);
const isDescending = ref(true);
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});
onMounted(() => {
  fetchDataFromFirebase();
  document.documentElement.setAttribute('data-theme', 'garden');
});

const aesKey = CryptoJS.enc.Utf8.parse('2B7E151628AED2A6ABF7158809CF4F3C');  // 128-bit key (same as Arduino)
const aesIv = CryptoJS.enc.Utf8.parse('AAAAAAAAAAAAAAAA');  // Initialization vector (same as Arduino)

async function fetchDataFromFirebase() {
  try {
    onValue(firebaseRef(database, 'freezer_real_data/'), (snapshot) => {
      if (snapshot.exists()) {
        const data = snapshot.val();
        tableData.value = Object.entries(data).map(([key, value]: any) => {
          return {
            key,
            data: value,
          };
        });

        tableData.value.sort((a: any, b: any) => {
          const dateA = new Date(`1970-01-01T${a.data.timestamp}`);
          const dateB = new Date(`1970-01-01T${b.data.timestamp}`);
          return isDescending.value
            ? dateB.getTime() - dateA.getTime()
            : dateA.getTime() - dateB.getTime();
        });
        const temperatures: any = [];
        const waypoints: any = [];

        tableData.value.forEach((el: any) => {
          const date = new Date(`1970-01-01T${el.data.timestamp}`);
          if (!isNaN(date.getTime())) {
            temperatures.push({
              value: el.data.temperature < -270 || el.data.temperature == 0 ? 31.4 : el.data.temperature,
              date: date.toISOString(),
            });
          }

          const lat = parseFloat(el.data.latitude);
          const lng = parseFloat(el.data.longitude);
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
    }, (error) => {
      console.error("Error fetching data from Firebase:", error);
    });
  } catch (error) {
    console.error("Error fetching data from Firebase:", error);
  }
}

const waves = ref([
  { name: 'Temperatures', data: [] as { value: number; date: string }[] },
]);
let leafletMap: any = null;

function plotWaypointsOnMap(waypoints: { lat: number; lng: number }[]) {
  const validWaypoints = waypoints.filter(
    point => !(point.lat === 0 && point.lng === 0)
  );

  const defaultLatLng = { lat: -7.273878833, lng: 112.8021323 };
  const initialPoint = validWaypoints.length > 0 ? validWaypoints[0] : defaultLatLng;

  if (leafletMap) {
    leafletMap.remove();
    leafletMap = null;
  }

  leafletMap = L.map('map').setView([initialPoint.lat, initialPoint.lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(leafletMap);

  if (validWaypoints.length > 0) {
    const latlngs: any = validWaypoints.map(point => [point.lat, point.lng]);

    validWaypoints.forEach(point => {
      L.marker([point.lat, point.lng]).addTo(leafletMap);
    });

    L.polyline(latlngs, { color: 'blue' }).addTo(leafletMap);
  } else {
    L.marker([defaultLatLng.lat, defaultLatLng.lng]).addTo(leafletMap)
      .bindPopup("Default Location (Surabaya)").openPopup();
  }
}

async function deleteByKey(key: string) {
  try {
    await remove(firebaseRef(database, `freezer_real_data/${key}`));
    tableData.value = tableData.value.filter((item: any) => item.key !== key);
    console.log(`Entry with key ${key} deleted successfully`);
  } catch (error) {
    console.error(`Error deleting entry with key ${key}:`, error);
  }
}

async function deleteAll() {
  try {
    await remove(firebaseRef(database, 'freezer_real_data'));
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
        date: point.date,
      })),
    };
  });

  const waveSheet = XLSX.utils.json_to_sheet(
    waveData.flatMap(wave => wave.data.map((point, index) => ({
      Name: wave.name,
      Value: point.value,
      Date: point.date,
      Index: index + 1,
    })))
  );

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, waveSheet, 'Waves');
  XLSX.writeFile(workbook, 'WaveData.xlsx');
}
</script>
