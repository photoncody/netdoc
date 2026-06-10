import re

with open("app/static/index.html", "r") as f:
    content = f.read()

networks_modal_template = """
        <!-- Networks Modal -->
        <div v-if="showNetworksModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" style="display: flex !important;">
            <div class="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-3xl flex flex-col border dark:border-gray-800" style="max-height: 90vh;">
                <div class="p-4 border-b dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50 rounded-t-lg shrink-0">
                    <h2 class="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2"><i data-lucide="globe" class="w-5 h-5 text-blue-500"></i> Location Networks</h2>
                    <button @click="showNetworksModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition"><i data-lucide="x" class="w-5 h-5"></i></button>
                </div>

                <div class="p-4 overflow-y-auto flex-1 text-sm text-gray-700 dark:text-gray-300 space-y-4">
                    <div class="bg-gray-100 dark:bg-gray-800 p-3 rounded flex gap-2 items-end">
                        <div class="flex-1 space-y-1"><label class="text-xs uppercase font-bold text-gray-500">Location Name</label><input v-model="networkForm.location" placeholder="e.g. 521 House" class="w-full bg-white dark:bg-gray-900 border dark:border-gray-700 rounded p-1.5"></div>
                        <div class="flex-1 space-y-1"><label class="text-xs uppercase font-bold text-gray-500">Subnet (CIDR)</label><input v-model="networkForm.subnet" placeholder="e.g. 192.168.1.0/24" class="w-full bg-white dark:bg-gray-900 border dark:border-gray-700 rounded p-1.5"></div>
                        <div class="flex-1 space-y-1"><label class="text-xs uppercase font-bold text-gray-500">Description</label><input v-model="networkForm.description" placeholder="Optional" class="w-full bg-white dark:bg-gray-900 border dark:border-gray-700 rounded p-1.5"></div>
                        <button @click="saveNetwork" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded transition h-[34px]">{{ networkForm.id ? 'Update' : 'Add' }}</button>
                        <button v-if="networkForm.id" @click="networkForm = {id: null, location: '', subnet: '', description: ''}" class="bg-gray-400 hover:bg-gray-500 text-white px-2 py-1.5 rounded transition h-[34px]"><i data-lucide="x" class="w-4 h-4"></i></button>
                    </div>

                    <table class="w-full border-collapse">
                        <thead>
                            <tr class="border-b-2 dark:border-gray-700 text-left bg-gray-50 dark:bg-gray-800">
                                <th class="p-2">Location</th>
                                <th class="p-2">Subnet</th>
                                <th class="p-2">Description</th>
                                <th class="p-2 w-16">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="net in locationNetworks" :key="net.id" class="border-b dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                <td class="p-2 font-medium">{{ net.location }}</td>
                                <td class="p-2 font-mono text-xs">{{ net.subnet }}</td>
                                <td class="p-2">{{ net.description }}</td>
                                <td class="p-2 flex gap-2">
                                    <button @click="networkForm = {...net}" class="text-blue-500 hover:text-blue-600"><i data-lucide="edit-2" class="w-4 h-4"></i></button>
                                    <button @click="deleteNetwork(net.id)" class="text-red-500 hover:text-red-600"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
                                </td>
                            </tr>
                            <tr v-if="locationNetworks.length === 0">
                                <td colspan="4" class="p-4 text-center text-gray-500 italic">No networks defined.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
"""

# Seems the previous patch failed to insert the modal template properly because <!-- Import Modal --> wasn't found or was altered.
# Let's insert it before <!-- Connections Modal -->
content = content.replace("<!-- Connections Modal -->", networks_modal_template + "\n        <!-- Connections Modal -->")

with open("app/static/index.html", "w") as f:
    f.write(content)
