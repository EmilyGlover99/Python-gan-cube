import { connectGanCube } from 'gan-web-bluetooth';

const connectButton = document.querySelector('#connect');
const output = document.querySelector('#output');

function print(message) {
  output.textContent += message + '\n';
}

connectButton.addEventListener('click', async () => {
  try {
    print("Choose the GAAN cube in the Bluetooth window.");
    const cube = await connectGanCube();
    print("Connected to GAAN cube!");
    print("Battery level: " + cube.batteryLevel + "%");

    cube.events$.subscribe(event => {
      if (event.type === 'MOVE') {
        print("Cube moved: " + event.move);
      }
      if (event.type === 'FACELETS') {
        print("Facelets updated: " + event.facelets);
      }
    });

      await cube.sendCubeCommand({ type: 'REQUEST_FACELETS' });
      print("Requested facelets update from the cube.");
    } catch (error) {
    print("Error: " + error.message);
  }
});
