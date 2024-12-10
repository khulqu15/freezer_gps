<template>
    <ion-page>
        <ion-content :fullscreen="true">
            <div class="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-primary to-primary/20 text-base-content">
                <div class="bg-white shadow-xl rounded-xl p-8 text-center w-96">
                    <h2 class="text-3xl font-bold mb-2 text-gray-700">Login</h2>
                    <p class="text-sm text-gray-500 mb-6">Freezer GPS App</p>
                    <div class="text-left mb-4">
                        <label for="email">Email</label>
                        <input v-model="email" type="email" class="mb-3 input input-bordered bg-base-100 w-full">
                        <label for="email">Password</label>
                        <input v-model="password" type="password" class="input input-bordered bg-base-100 w-full">
                    </div>
                    <button @click="loginWithEmail" class="flex items-center justify-center w-full bg-primary text-white font-semibold py-2 rounded-lg shadow hover:bg-blue-700 transition-colors">
                        Login
                    </button>
                </div>
            </div>
        </ion-content>
    </ion-page>
</template>


<script setup lang="ts">
import CardViewVue from '@/components/CardView.vue';
import { IonContent, IonPage } from '@ionic/vue';
import { database, ref as firebaseRef, get, update, auth } from '@/firebaseConfig';
import { onValue, set } from 'firebase/database';
import { onMounted } from 'vue';
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { useRouter } from "vue-router";
import { ref } from 'vue';

const email = ref('');
const password = ref('');

onMounted(() => {
    document.documentElement.setAttribute('data-theme', 'garden')
    const user = sessionStorage.getItem('user');
    console.log(user)
    if (user) {
        router.push({ name: 'Home' });
    }
});
const router = useRouter()

async function loginWithGoogle() {
  const provider = new GoogleAuthProvider();
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    sessionStorage.setItem('user', JSON.stringify({
      displayName: user.displayName,
      email: user.email,
      photoURL: user.photoURL,
      uid: user.uid
    }));

    console.log('User signed in:', user);
    alert('Login successful');
    router.push({name: 'Home'})
  } catch (error) {
    console.error('Error during login:', error);
    alert('Login failed');
  }
}
  
function loginWithEmail() {
    if(email.value == 'riofajar120@gmail.com' && password.value == '12345678') {
        sessionStorage.setItem('user', JSON.stringify({
            displayName: 'Rio Fajar',
            email: 'riofajar120@gmail.com',
            photoURL: '',
            uid: 'adnjadiubadknaduih2y8gabxcjkadolkj'
        }));
        router.push({name: 'Home'})
    } else {
        alert('Login failed');
    }
    alert('Login successful');
    router.push({name: 'Home'})
}

</script>