![alt text|80](/images/AOP-networkFinder_for_paper.jpg)
Graphic mark of "AOP-networkFinder. Green represent Molecular Initiation Events (MIEs) in the Adverse Outcome Pathway (AOP). Orange represents adherent Key Events (KEs). Red triangles represent Adverse Outcomes (AOs), at the end of the path.
The arrows illustrate the direction of Key Events Relationships (KERs). Blue circles represent genes connected to KEs.
Notice that this representation is in form a Directed Acyclic Graph (DAG) with no directed cycles.


## Web-Application AOP-networkFinder v2 is available under:
## https://aop-networkfinder.no/

Please cite the AOP-networkFinder:
BIORXIV/2024/591733  "AOP-networkFinder v2- A versatile and user-friendly tool for FAIR reconstruction of Adverse Outcome Pathway networks from the AOP-Wiki"
Authors: Igor Momcilovic, Sara Dugalic, Nurettin Yarar, Marvin Martens, Torbjørn Rognes, Jan Lavender, Hubert Dirven, Karine Audouze and Marcin W. Wojewodzic#

Corresponding author: Marcin W. Wojewodzic (Email: maww [at] fhi.no)

1. Find the status of all AOPs in the webpage AOPWiki.org/aops (OECD Status)

The Current GUI of the AOP_Visualizer webpage:

![main window]![MixCollage-30-Apr-2025-01-45-PM-9326](https://github.com/user-attachments/assets/67fe1a2a-3e5d-4d01-8ff2-91882a056574)



2. How to run the application locally using Docker

## Prerequisites
Docker is installed on your system.

## Running the project locally
1. Clone the repository
2. Navigate to the project directory
3. Create a .env File
   In the root directory of the project, create a .env file with the following content:
```
EPA_API_KEY=****
```
4. Run the following command to build the Docker image:
```
 docker compose up --build     
 ```
5. The application should be running on port 8000. If you change something in the code, it should reload automatically. Just refresh the page in your browser, and it should be updated.
6. To stop the application, run the following command:
```
docker compose down
```


To access the application locally:
http://localhost:8000

You should see a window similar to this:
![main window](https://github.com/user-attachments/assets/6f0ef637-f6e9-4ff9-bca5-24796c8d45f3)


3. App architecture
   ![Arch overview](https://github.com/user-attachments/assets/424e287b-ddff-4af1-a892-68b98930c42f)

4. Flow diagram of main flow
   ![smartflowdiagramAOP](https://github.com/user-attachments/assets/a870fe79-06a9-4e3a-8b0e-60dbf9e2d62e)


   

